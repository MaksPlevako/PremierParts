"""Preview and apply the supplier's semicolon-separated wholesale price list."""

import csv
import hashlib
import io
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from apps.core.revalidate import revalidate_tags

from .models import Product


MAX_PRICE = Decimal("99999999.99")
CENT = Decimal("0.01")
BRAND_ALIASES = {"XINYI": "XYG", "KLOKKER": "KLOKKERHOLM", "KOYOAIR": "KOYORAD"}


class SupplierPriceError(ValueError):
    pass


def normalize_sku(value: str) -> str:
    # Preserve Cyrillic suffixes such as "_УЦН": they identify distinct stock.
    return "".join(char for char in (value or "").upper() if char.isalnum())


def normalize_brand(value: str) -> str:
    return "".join(char for char in (value or "").upper() if char.isalnum())


@dataclass(frozen=True)
class PriceChange:
    product_id: int
    sku: str
    brand: str
    old_price: Decimal
    new_price: Decimal
    old_supplier_price: Decimal | None
    new_supplier_price: Decimal


@dataclass
class PricePlan:
    rows: int = 0
    matched_rows: int = 0
    unmatched_rows: int = 0
    invalid_rows: int = 0
    conflicting_rows: int = 0
    duplicate_rows: int = 0
    matched_products: int = 0
    retail_changes: int = 0
    baseline_products: int = 0
    changes: list[PriceChange] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    fingerprint: str = ""

    def issue(self, message: str) -> None:
        if len(self.issues) < 25:
            self.issues.append(message)


def _parse_price(raw: str) -> Decimal:
    value = (raw or "").strip().replace("\u00a0", "").replace(" ", "").replace(",", ".")
    try:
        price = Decimal(value).quantize(CENT)
    except (InvalidOperation, ValueError):
        raise SupplierPriceError(f"некоректна ціна «{raw}»") from None
    if not price.is_finite() or price <= 0 or price > MAX_PRICE:
        raise SupplierPriceError(f"ціна поза допустимим діапазоном «{raw}»")
    return price


def _decode(data: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1251"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise SupplierPriceError("Файл має невідому кодову сторінку")


def build_supplier_price_plan(data: bytes, mode: str = "preserve_margin", *, lock: bool = False) -> PricePlan:
    if mode not in {"preserve_margin", "supplier_as_retail"}:
        raise SupplierPriceError("Невідомий спосіб розрахунку цін")
    if not data:
        raise SupplierPriceError("Файл порожній")
    try:
        reader = csv.DictReader(io.StringIO(_decode(data), newline=""), delimiter=";", strict=True)
        if not reader.fieldnames or not {"Brand", "ItemNo", "Price"}.issubset(reader.fieldnames):
            raise SupplierPriceError("Потрібен прайс постачальника з колонками Brand;ItemNo;Price")

        plan = PricePlan()
        rows_by_key = defaultdict(list)
        for row in reader:
            plan.rows += 1
            item_no = (row.get("ItemNo") or "").strip()
            brand = (row.get("Brand") or "").strip()
            sku_key = normalize_sku(item_no)
            brand_key = BRAND_ALIASES.get(normalize_brand(brand), normalize_brand(brand))
            if None in row or not sku_key or not brand_key:
                plan.invalid_rows += 1
                plan.issue(f"Рядок {reader.line_num}: бракує артикула/бренду або зайві колонки")
                continue
            try:
                price = _parse_price(row.get("Price"))
            except SupplierPriceError as exc:
                plan.invalid_rows += 1
                plan.issue(f"Рядок {reader.line_num}, {item_no}: {exc}")
                continue
            rows_by_key[(sku_key, brand_key)].append((item_no, price, reader.line_num))
    except (csv.Error, UnicodeError) as exc:
        raise SupplierPriceError(f"Не вдалося прочитати CSV: {exc}") from exc

    products_by_key = defaultdict(list)
    products = Product.objects.select_for_update(of=("self",)) if lock else Product.objects
    for product in products.values("id", "sku", "manufacturer__name", "price", "supplier_price"):
        key = (normalize_sku(product["sku"]), normalize_brand(product["manufacturer__name"]))
        if key[0] and key[1]:
            products_by_key[key].append(product)

    digest = hashlib.sha256(data)
    digest.update(mode.encode("ascii"))
    for key, entries in rows_by_key.items():
        prices = {entry[1] for entry in entries}
        if len(prices) > 1:
            plan.conflicting_rows += len(entries)
            plan.issue(f"{entries[0][0]}: різні ціни для одного артикула й бренду; усі рядки пропущено")
            continue
        plan.duplicate_rows += len(entries) - 1
        matched = products_by_key.get(key, [])
        if not matched:
            plan.unmatched_rows += len(entries)
            plan.issue(f"{entries[0][0]} ({key[1]}): товар не знайдено")
            continue
        plan.matched_rows += 1
        plan.matched_products += len(matched)
        cost = entries[0][1]
        for product in matched:
            old_price = product["price"]
            old_cost = product["supplier_price"]
            if mode == "supplier_as_retail":
                new_price = cost
            elif old_cost and old_cost > 0:
                new_price = (old_price * cost / old_cost).quantize(CENT, rounding=ROUND_HALF_UP)
            else:
                new_price = old_price
                plan.baseline_products += 1
            if new_price > MAX_PRICE:
                plan.invalid_rows += 1
                plan.issue(f"{entries[0][0]}: роздрібна ціна перевищує допустимий діапазон")
                continue
            digest.update(f"|{product['id']}:{old_price}:{old_cost}:{new_price}:{cost}".encode("utf-8"))
            if new_price != old_price:
                plan.retail_changes += 1
            if new_price != old_price or old_cost != cost:
                plan.changes.append(
                    PriceChange(product["id"], product["sku"], product["manufacturer__name"],
                                old_price, new_price, old_cost, cost)
                )
    plan.fingerprint = digest.hexdigest()
    return plan


def apply_supplier_price_plan(plan: PricePlan) -> int:
    """Call inside the transaction used to build a locked plan."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Імпорт цін потребує транзакції")
    if not plan.changes:
        return 0
    now = timezone.now()
    updates = [
        Product(id=change.product_id, price=change.new_price,
                supplier_price=change.new_supplier_price, updated_at=now)
        for change in plan.changes
    ]
    Product.objects.bulk_update(updates, ["price", "supplier_price", "updated_at"], batch_size=500)
    if plan.retail_changes:
        revalidate_tags(["products", "home"])
    return len(updates)
