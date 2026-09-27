"""Idempotent catalog writes for a single Forma category, item, or vehicle."""

import hashlib
from collections import defaultdict

from django.utils import timezone

from apps.catalog.models import (
    CarModel, Category, Fitment, Generation, Make, Manufacturer, Product, StockStatus,
)
from apps.core.normalize import slugify_uk

from .client import FormaAPIError
from .models import (
    FormaAttributeName, FormaCategory, FormaItem, FormaItemAttribute,
    FormaVehicleFitment, FormaVehicleType, FormaWarehouseStock,
)
from .normalize import (
    as_bool, category_nodes, clean_name, item_available, item_key,
    key_text, money, parse_stock, positive_type_id, vehicle_key,
)

BRAND_ALIASES = {"XINYI": "XYG", "KLOKKER": "KLOKKERHOLM", "KOYOAIR": "KOYORAD"}
VEHICLE_SPEC_FIELDS = (
    "bodyType", "capacity", "ccmTech", "cylinders", "driveType", "engineType", "engines",
    "fuel", "fuelPreparation", "hp", "kw", "tonnage", "valve", "image",
)


def brand_key(value: str) -> str:
    key = "".join(ch for ch in clean_name(value).upper() if ch.isalnum())
    return BRAND_ALIASES.get(key, key)


class FormaDataError(FormaAPIError):
    pass


def _unique_slug(prefix: str, value: str, model, *, max_length: int) -> str:
    base = (slugify_uk(value) or prefix)[:max_length]
    if not model.objects.filter(slug=base).exists():
        return base
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    return f"{base[:max_length - 9]}-{digest}"


def sync_categories(payload, *, seen_at=None) -> list[FormaCategory]:
    seen_at = seen_at or timezone.now()
    links_by_id = {}
    leaves = []
    for raw, parent_external_id, order, is_leaf in category_nodes(payload):
        external_id = raw["id"]
        title = clean_name(raw.get("title"))
        if not title:
            raise FormaDataError(f"Forma category {external_id} не має title")
        if len(title) > 160:
            raise FormaDataError(f"Forma category {external_id}: title занадто довгий")
        parent = links_by_id[parent_external_id].category if parent_external_id else None
        link = FormaCategory.objects.select_related("category").filter(external_id=external_id).first()
        if link:
            category = link.category
            if category.slug.startswith("forma-"):
                category.parent = parent
                category.sort = order
                category.save(update_fields=["parent", "sort"])
        else:
            category = Category.objects.filter(parent=parent, name__iexact=title).exclude(forma_link__isnull=False).first()
            if category is None:
                category = Category.objects.create(
                    parent=parent, name=title, slug=f"forma-{external_id}", sort=order,
                )
            link = FormaCategory(external_id=external_id, category=category)
        link.title = title
        link.source_image_path = clean_name(raw.get("img"))[:500]
        link.item_group = clean_name(raw.get("itemGroup"))[:160]
        link.item_sub_group = clean_name(raw.get("itemSubGroup"))[:160]
        link.is_leaf = is_leaf
        link.active = as_bool(raw.get("active", True))
        link.raw_data = raw
        link.last_seen_at = seen_at
        link.save()
        links_by_id[external_id] = link
        if is_leaf and link.active:
            leaves.append(link)
    return leaves


class ProductMatcher:
    def __init__(self):
        self.by_key = defaultdict(list)
        for product in Product.objects.select_related("manufacturer").all():
            if product.sku and product.manufacturer_id:
                self.by_key[(item_key(product.sku), brand_key(product.manufacturer.name))].append(product)

    def match(self, sku: str, brand: str) -> Product | None:
        matches = self.by_key.get((item_key(sku), brand_key(brand)), [])
        if len(matches) > 1:
            raise FormaDataError(f"Неоднозначний артикул і бренд: {sku} / {brand}")
        if matches and hasattr(matches[0], "forma_item"):
            return None
        return matches[0] if matches else None

    def add(self, product: Product):
        self.by_key[(item_key(product.sku), brand_key(product.manufacturer.name))].append(product)


def _manufacturer(name: str) -> Manufacturer:
    existing = Manufacturer.objects.filter(name__iexact=name).first()
    if existing:
        return existing
    slug = _unique_slug("forma-brand", name, Manufacturer, max_length=80)
    return Manufacturer.objects.create(name=name, slug=slug)


def _product_text(raw: dict, sku: str, brand: str) -> tuple[str, str]:
    name = clean_name(raw.get("description") or raw.get("searchDescription") or raw.get("shortText"))
    description = "\n\n".join(
        dict.fromkeys(clean_name(raw.get(key)) for key in ("longText", "shortText", "criteriaLine") if raw.get(key))
    )
    return (name or f"{brand} {sku}")[:300], description


def _sync_attributes(item: FormaItem, raw: dict):
    criteria = raw.get("criterias") or []
    if not isinstance(criteria, list):
        raise FormaDataError(f"{item.item_no}: criterias не є списком")
    values = defaultdict(list)
    labels = {}
    for criterion in criteria:
        if not isinstance(criterion, dict):
            continue
        name = clean_name(criterion.get("criteria"))
        value = clean_name(criterion.get("value"))
        if name and value and value not in values[key_text(name)]:
            values[key_text(name)].append(value)
            labels[key_text(name)] = name
    seen = set()
    for key, parts in values.items():
        attribute, _ = FormaAttributeName.objects.get_or_create(
            normalized_name=key[:160], defaults={"name": labels[key][:160]},
        )
        FormaItemAttribute.objects.update_or_create(
            item=item, attribute=attribute, defaults={"value": ", ".join(parts)},
        )
        seen.add(attribute.id)
    item.attributes.exclude(attribute_id__in=seen).delete()


def _sync_stock(item: FormaItem, warehouses):
    seen = set()
    for warehouse in warehouses:
        FormaWarehouseStock.objects.update_or_create(
            item=item, location_code=warehouse.code[:120],
            defaults={
                "location_name": warehouse.name[:120],
                "quantity_raw": warehouse.quantity_raw[:40],
                "quantity_min": warehouse.quantity_min,
                "quantity_is_more_than": warehouse.more_than,
                "reserved_raw": warehouse.reserved_raw[:40],
                "raw_data": warehouse.raw,
            },
        )
        seen.add(warehouse.code[:120])
    item.warehouses.exclude(location_code__in=seen).delete()


def upsert_item(raw: dict, category: FormaCategory, matcher: ProductMatcher, *, seen_at=None, fast=False) -> tuple[FormaItem, bool]:
    if not isinstance(raw, dict):
        raise FormaDataError("Forma item не є об'єктом")
    sku = clean_name(raw.get("itemNo"))
    brand = clean_name(raw.get("brand"))
    normalized = item_key(sku)
    if not normalized or not brand:
        raise FormaDataError("Forma item бракує itemNo або brand")
    if len(normalized) > 80 or len(sku) > 80 or len(brand) > 80:
        raise FormaDataError(f"Forma itemNo/brand занадто довгі: {sku[:60]}")
    warehouses = parse_stock(raw.get("stock"))
    retail = money(raw.get("retail"))
    customer_price = money(raw.get("price"))
    if raw.get("retail") not in (None, "") and retail is None:
        raise FormaDataError(f"{sku}: некоректна retail ціна")
    existing = FormaItem.objects.select_related("product").filter(normalized_item_no=normalized).first()
    price_stock_only = fast and existing is not None
    created_product = False
    if existing:
        product = existing.product
        if product.manufacturer_id and brand_key(product.manufacturer.name) != brand_key(brand):
            raise FormaDataError(f"{sku}: бренд змінився з {product.manufacturer.name} на {brand}")
    else:
        product = matcher.match(sku, brand)
        if product is None:
            manufacturer = _manufacturer(brand)
            name, description = _product_text(raw, sku, brand)
            product = Product.objects.create(
                name=name, slug=f"forma-{hashlib.sha1(normalized.encode('utf-8')).hexdigest()[:20]}",
                sku=sku, manufacturer=manufacturer, category=category.category,
                description=description, price=retail or 0,
                stock_status=StockStatus.IN_STOCK if item_available(raw, warehouses) else StockStatus.OUT_OF_STOCK,
            )
            created_product = True
        existing = FormaItem(product=product, normalized_item_no=normalized)

    if not price_stock_only:
        if created_product or not product.legacy_url:
            name, description = _product_text(raw, sku, brand)
            product.name = name
            product.description = description
            product.category = category.category
        elif not product.description:
            product.description = _product_text(raw, sku, brand)[1]
    if retail is not None:
        product.price = retail
    product.stock_status = StockStatus.IN_STOCK if item_available(raw, warehouses) else StockStatus.OUT_OF_STOCK
    product.save()

    existing.item_no = sku
    if not price_stock_only:
        existing.category = category
    existing.supplier_customer_price = customer_price
    existing.retail_price = retail
    existing.quantity_raw = clean_name(raw.get("quantity"))[:40]
    existing.in_stock = as_bool(raw.get("inStock"))
    existing.discontinued = as_bool(raw.get("discontinued"))
    if not price_stock_only:
        existing.short_text = clean_name(raw.get("shortText"))
        existing.search_description = clean_name(raw.get("searchDescription"))
        existing.criteria_line = clean_name(raw.get("criteriaLine"))
    existing.raw_data = raw
    existing.last_seen_at = seen_at or timezone.now()
    existing.save()
    if not price_stock_only:
        _sync_attributes(existing, raw)
    _sync_stock(existing, warehouses)
    if created_product:
        matcher.add(product)
    return existing, created_product


def _make(name: str) -> Make:
    existing = Make.objects.filter(name__iexact=name).first()
    if existing:
        return existing
    return Make.objects.create(name=name, slug=_unique_slug("forma-make", name, Make, max_length=80))


def _model(make: Make, name: str) -> CarModel:
    existing = CarModel.objects.filter(make=make, name__iexact=name).first()
    if existing:
        return existing
    slug = _unique_slug("forma-model", f"{make.name}-{name}", CarModel, max_length=140)
    return CarModel.objects.create(make=make, name=name, slug=slug)


def upsert_vehicle_fitment(item: FormaItem, raw: dict, *, seen_at=None) -> bool:
    if not isinstance(raw, dict):
        raise FormaDataError(f"{item.item_no}: vehicle не є об'єктом")
    key = vehicle_key(raw)
    mark = clean_name(raw.get("mark"))
    model_name = clean_name(raw.get("model"))
    if not mark or not model_name:
        raise FormaDataError(f"{item.item_no}: vehicle бракує mark/model")
    if len(mark) > 80 or len(model_name) > 120:
        raise FormaDataError(f"{item.item_no}: vehicle mark/model занадто довгі")
    now = seen_at or timezone.now()
    vehicle = FormaVehicleType.objects.select_related("generation").filter(key=key).first()
    if vehicle is None:
        make = _make(mark)
        car_model = _model(make, model_name)
        source_label = clean_name(raw.get("typeName"))[:120]
        slug = f"forma-{hashlib.sha1(key.encode('utf-8')).hexdigest()[:20]}"
        generation = Generation.objects.create(model=car_model, slug=slug, source_label=source_label)
        type_id = positive_type_id(raw.get("typeId"))
        vehicle = FormaVehicleType.objects.create(
            key=key, external_type_id=type_id,
            generation=generation, type_name=source_label, type_range=clean_name(raw.get("typeRange"))[:120],
            specs={field: raw[field] for field in VEHICLE_SPEC_FIELDS if field in raw},
            raw_data=raw, last_seen_at=now,
        )
    else:
        vehicle.type_name = clean_name(raw.get("typeName"))[:120]
        vehicle.type_range = clean_name(raw.get("typeRange"))[:120]
        vehicle.specs = {field: raw[field] for field in VEHICLE_SPEC_FIELDS if field in raw}
        vehicle.raw_data = raw
        vehicle.last_seen_at = now
        vehicle.save(update_fields=["type_name", "type_range", "specs", "raw_data", "last_seen_at"])
        if vehicle.type_name != vehicle.generation.source_label:
            vehicle.generation.source_label = vehicle.type_name
            vehicle.generation.save(update_fields=["source_label"])
    _, created = FormaVehicleFitment.objects.update_or_create(
        item=item, vehicle=vehicle, defaults={"raw_data": raw, "last_seen_at": now},
    )
    Fitment.objects.get_or_create(product=item.product, generation=vehicle.generation)
    return created
