"""Validate and normalize the documented Forma payload fields."""

import json
import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .client import FormaAPIError


MAX_MONEY = Decimal("99999999.99")


def clean_name(value) -> str:
    return " ".join(str("" if value is None else value).split())


def key_text(value) -> str:
    return clean_name(value).casefold()


def item_key(value) -> str:
    return "".join(ch for ch in clean_name(value).upper() if ch.isalnum())


def money(value) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        result = Decimal(str(value).strip().replace("\u00a0", "").replace(" ", "").replace(",", "."))
        result = result.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() and 0 <= result <= MAX_MONEY else None


def as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes"}
    return bool(value)


@dataclass(frozen=True)
class Warehouse:
    code: str
    name: str
    quantity_raw: str
    quantity_min: int | None
    more_than: bool
    reserved_raw: str
    raw: dict


def parse_quantity(value) -> tuple[int | None, bool]:
    raw = clean_name(value)
    match = re.fullmatch(r"(>)?\s*(\d+)", raw)
    if not match:
        return None, False
    number = int(match.group(2))
    return (number + 1 if match.group(1) else number), bool(match.group(1))


def parse_stock(value) -> list[Warehouse]:
    if value in (None, ""):
        return []
    try:
        payload = json.loads(value) if isinstance(value, str) else value
    except ValueError as exc:
        raise FormaAPIError("Forma stock містить некоректний JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("Stock", []), list):
        raise FormaAPIError("Forma stock має невідому структуру")
    warehouses = []
    for index, row in enumerate(payload.get("Stock", [])):
        if not isinstance(row, dict):
            continue
        code = clean_name(row.get("C") or row.get("L")) or f"unknown-{index}"
        raw = clean_name(row.get("Q"))
        quantity_min, more_than = parse_quantity(raw)
        warehouses.append(Warehouse(
            code=code, name=clean_name(row.get("L")), quantity_raw=raw,
            quantity_min=quantity_min, more_than=more_than,
            reserved_raw=clean_name(row.get("R")), raw=row,
        ))
    return warehouses


def item_available(item: dict, warehouses: list[Warehouse]) -> bool:
    if as_bool(item.get("discontinued")):
        return False
    return any((warehouse.quantity_min or 0) > 0 for warehouse in warehouses) or as_bool(item.get("inStock"))


def category_nodes(payload):
    """Return depth-first (node, parent external ID, sort, is_leaf) tuples."""
    roots = payload if isinstance(payload, list) else payload.get("childElements") if isinstance(payload, dict) and "id" not in payload else [payload]
    if not isinstance(roots, list):
        raise FormaAPIError("Forma category tree має невідому структуру")
    seen = set()

    def visit(node, parent_id=None, sort=0):
        if not isinstance(node, dict):
            raise FormaAPIError("Forma category node не є об'єктом")
        external_id = node.get("id")
        if isinstance(external_id, bool) or not isinstance(external_id, int) or external_id <= 0:
            raise FormaAPIError("Forma category node не має валідного id")
        if external_id in seen:
            raise FormaAPIError(f"Forma category tree має повторний id {external_id}")
        seen.add(external_id)
        children = node.get("childElements") or []
        if not isinstance(children, list):
            raise FormaAPIError(f"Forma category {external_id}: childElements не є списком")
        supplier_sort = node.get("sort")
        order = supplier_sort if isinstance(supplier_sort, int) and not isinstance(supplier_sort, bool) and supplier_sort >= 0 else sort
        yield (node, parent_id, order, not children)
        for index, child in enumerate(children):
            yield from visit(child, external_id, index)

    for index, root in enumerate(roots):
        yield from visit(root, None, index)


def vehicle_key(vehicle: dict) -> str:
    type_id = positive_type_id(vehicle.get("typeId"))
    if type_id:
        return f"id:{type_id}"
    parts = [key_text(vehicle.get(field)) for field in ("mark", "model", "typeName", "typeRange")]
    if not parts[0] or not parts[1] or not any(parts[2:]):
        raise FormaAPIError("Forma vehicle бракує mark/model/typeName або typeId")
    joined = "name:" + "|".join(parts)
    return joined if len(joined) <= 240 else "name-sha256:" + hashlib.sha256(joined.encode("utf-8")).hexdigest()


def positive_type_id(value) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str) and value.isdecimal() and int(value) > 0:
        return int(value)
    return None


def unwrap_list(payload, *keys: str) -> list:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in keys:
            if isinstance(payload.get(key), list):
                return payload[key]
    raise FormaAPIError("Forma API повернув невідомий формат списку")
