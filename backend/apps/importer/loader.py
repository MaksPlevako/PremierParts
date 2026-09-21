"""Idempotent upserts of parsed legacy data into the catalog."""

import hashlib
from pathlib import Path

from django.conf import settings
from django.db import transaction

from apps.catalog.models import (
    CarModel,
    Category,
    Fitment,
    Generation,
    Make,
    Manufacturer,
    PartNumber,
    PartNumberKind,
    Product,
    ProductImage,
    StockStatus,
)
from apps.core.normalize import normalize_part_number, slugify_uk, split_part_numbers

from .parsers import CategoryNode, ModelLink, ParsedProduct, parse_side_position, parse_years

MAKE_ALIASES = {"Porshe": "Porsche", "Ssang Yong": "SsangYong", "Mercedes": "Mercedes-Benz", "VW": "Volkswagen"}

TOP_CATEGORY_ICONS = {
    "Оптика": "light",
    "Кузов": "body",
    "Радіатори": "radiator",
    "Дзеркала бічні": "mirror",
    "Дзеркала": "mirror",
    "Автоскло": "glass",
    "Вихлопна система": "exhaust",
}

TOP_CATEGORY_SLUGS = {
    "Оптика": "optika",
    "Кузов": "kuzov",
    "Радіатори": "radiatory-avtomobilnye",
    "Дзеркала бічні": "zerkala-bokovye",
    "Автоскло": "avtostekla",
    "Вихлопна система": "vyhlopna_systema",
}

CHILD_CATEGORY_ICONS = {
    "fary-perednie": "headlight",
    "fonari-zadnie": "taillight",
    "protivotumannye-fary": "foglight",
    "ukazateli-povorotov": "turn-signal",
    "kapoty": "hood",
    "panel-radiatora-ustanovochnaya-panel-televizor": "panel",
    "krylya-perednie": "fender",
    "pidsilyuvach-absorber-bampera": "bumper",
    "dveri": "door",
    "reshetki-ramki-nakladki": "grille",
    "arki-krylev-porogi-remchasti": "fender",
    "bamper-komplektuyushie": "bumper",
    "kryshki-bagazhnika": "trunk",
    "zashita-dvigatelya-zashita-bampera-plastik": "shield",
    "pidkrilki-avtomobilni-lokeri": "fender",
    "balki-podramniki": "frame",
    "amortizatory-kapota-bagazhnika": "strut",
    "bachki-rasshiritelnye-i-omyvatelya": "tank",
    "radiatory-ohlazhdeniya": "radiator",
    "radiatory-kondicionera": "radiator",
    "ventilyatory-ohlazhdeniya-radiatora": "fan",
    "radiatory-pechki": "radiator",
    "interkuler": "radiator",
    "maslyanye-radiatory-teploobmenniki": "radiator",
    "osushiteli-kondicionera": "tank",
    "zerkala-bokovye": "mirror",
    "zerkalo-v-sbore": "mirror",
    "vkladysh-zerkala": "mirror",
    "vkladysh-zerkala-zerkalnyj-element": "mirror",
    "steklo-lobovoe": "glass",
    "steklo-zadnee": "glass",
    "steklo-bokovoe-dver-kuzov": "glass",
    "steklopodemniki": "window-lift",
    "derzhateli-shetki-dvornikov": "wiper",
    "vyhlopna_systema": "exhaust",
}


def canonical_make_name(name: str) -> str:
    name = (name or "").strip()
    return MAKE_ALIASES.get(name, name)


def upsert_make(legacy_id: int | None, name: str) -> Make:
    canonical = canonical_make_name(name)
    make = Make.objects.filter(name__iexact=canonical).first()
    if make is None:
        make = Make.objects.create(
            name=canonical,
            slug=slugify_uk(canonical),
            legacy_id=legacy_id if canonical == name else None,
        )
    elif legacy_id and make.legacy_id is None and canonical == name:
        make.legacy_id = legacy_id
        make.save(update_fields=["legacy_id"])
    return make


def _car_model(make: Make, name: str, legacy_id: int | None = None) -> CarModel:
    name = name.strip()
    model = CarModel.objects.filter(make=make, name__iexact=name).first()
    if model is None:
        base_slug = slugify_uk(name) or "model"
        slug = base_slug
        n = 2
        while CarModel.objects.filter(make=make, slug=slug).exists():
            slug = f"{base_slug}-{n}"
            n += 1
        model = CarModel.objects.create(make=make, name=name, slug=slug, legacy_id=legacy_id)
    elif legacy_id and not model.legacy_id:
        model.legacy_id = legacy_id
        model.save(update_fields=["legacy_id"])
    return model


def _generation_slug(model: CarModel, years: tuple[int | None, int | None], suffix: str) -> str:
    y1, y2 = years
    base = f"{y1}-{y2}" if y1 and y2 else (f"{y1}" if y1 else "all")
    if not Generation.objects.filter(model=model, slug=base).exists():
        return base
    return f"{base}-{suffix}"


def _find_or_create_generation(model: CarModel, years, legacy_id: str = "") -> Generation:
    y1, y2 = years
    gen = Generation.objects.filter(model=model, year_from=y1, year_to=y2).first()
    if gen is None:
        gen = Generation.objects.create(
            model=model,
            year_from=y1,
            year_to=y2,
            slug=_generation_slug(model, years, legacy_id.split(":")[-1] or "x"),
            legacy_id=legacy_id,
        )
    elif legacy_id and not gen.legacy_id:
        gen.legacy_id = legacy_id
        gen.save(update_fields=["legacy_id"])
    return gen


def upsert_generation(make: Make, link: ModelLink) -> Generation:
    legacy_id = f"{link.model_legacy_id}:{link.series_legacy_id}"
    existing = Generation.objects.filter(legacy_id=legacy_id).select_related("model").first()
    if existing:
        return existing
    model = _car_model(make, link.model_name, link.model_legacy_id)
    return _find_or_create_generation(model, link.years, legacy_id)


def upsert_category_tree(nodes: list[CategoryNode]) -> dict[str, Category]:
    result: dict[str, Category] = {}
    for sort, node in enumerate(nodes):
        slug = node.slug or TOP_CATEGORY_SLUGS.get(node.name) or slugify_uk(node.name)
        parent = Category.objects.filter(parent__isnull=True, name=node.name).first()
        if parent is None:
            parent = Category.objects.create(
                name=node.name, slug=slug, icon=TOP_CATEGORY_ICONS.get(node.name, ""), sort=sort * 10
            )
        elif parent.slug != slug and not Category.objects.filter(slug=slug).exclude(pk=parent.pk).exists():
            parent.slug = slug
            parent.save(update_fields=["slug"])
        result[parent.slug] = parent
        for child_sort, child in enumerate(node.children):
            cat, _ = Category.objects.update_or_create(
                slug=child.slug,
                defaults={
                    "name": child.name,
                    "parent": parent,
                    "sort": child_sort * 10,
                    "icon": CHILD_CATEGORY_ICONS.get(child.slug, parent.icon),
                },
            )
            result[cat.slug] = cat
    return result


def ensure_category_path(crumbs: list[tuple[str, str]]) -> Category:
    """Make sure every breadcrumb category exists (with the legacy slug) and return the leaf."""
    parent: Category | None = None
    for name, slug in crumbs:
        cat = Category.objects.filter(slug=slug).first()
        if cat is None:
            same_name = Category.objects.filter(name=name, parent=parent).first()
            if same_name:
                same_name.slug = slug
                same_name.save(update_fields=["slug"])
                cat = same_name
            else:
                cat = Category.objects.create(
                    name=name,
                    slug=slug,
                    parent=parent,
                    icon=TOP_CATEGORY_ICONS.get(name) or CHILD_CATEGORY_ICONS.get(slug, ""),
                )
        parent = cat
    if parent is None:
        parent, _ = Category.objects.get_or_create(slug="inshe", defaults={"name": "Інше"})
    return parent


def _manufacturer(name: str | None) -> Manufacturer | None:
    name = (name or "").strip()
    if not name:
        return None
    found = Manufacturer.objects.filter(name__iexact=name).first()
    return found or Manufacturer.objects.create(name=name, slug=slugify_uk(name) or hashlib.sha1(name.encode()).hexdigest()[:8])


def _popularity(p: ParsedProduct) -> int:
    seed = int(hashlib.sha1((p.sku or p.slug).encode()).hexdigest()[:6], 16) % 100
    return seed + (60 if p.price > 0 and p.in_stock else 0) + (20 if p.image_urls else 0)


def _generation_for(p: ParsedProduct) -> Generation | None:
    if not (p.make and p.model):
        return None
    make = upsert_make(None, p.make)
    model = _car_model(make, p.model)
    years = parse_years(p.series or "")
    return _find_or_create_generation(model, years)


@transaction.atomic
def upsert_product(p: ParsedProduct, images: list[tuple[str, Path]]) -> Product:
    category = ensure_category_path(p.breadcrumbs)
    side, position = parse_side_position(p.name)
    defaults = {
        "name": p.name,
        "sku": p.sku,
        "category": category,
        "manufacturer": _manufacturer(p.manufacturer),
        "description": p.description,
        "price": p.price,
        "stock_status": StockStatus.IN_STOCK if p.in_stock and p.price > 0 else StockStatus.ON_ORDER,
        "side": side,
        "position": position,
        "condition": "new",
        "popularity": _popularity(p),
    }
    product = Product.objects.filter(legacy_url=p.url).first() or Product.objects.filter(slug=p.slug).first()
    if product:
        for key, value in defaults.items():
            setattr(product, key, value)
        product.legacy_url = p.url
        product.save()
    else:
        product = Product.objects.create(slug=p.slug, legacy_url=p.url, **defaults)

    gen = _generation_for(p)
    if gen:
        Fitment.objects.get_or_create(product=product, generation=gen)

    sku_norm = normalize_part_number(p.sku)
    wanted = {}
    if sku_norm:
        wanted[sku_norm] = (p.sku, PartNumberKind.SKU)
    for number in split_part_numbers(p.name):
        wanted.setdefault(number, (number, PartNumberKind.OEM))
    existing = set(product.part_numbers.values_list("normalized", flat=True))
    for normalized, (raw, kind) in wanted.items():
        if normalized not in existing:
            PartNumber.objects.create(product=product, number=raw, kind=kind)

    known = set(product.images.values_list("source_url", flat=True))
    media_root = Path(settings.MEDIA_ROOT)
    for sort, (url, path) in enumerate(images):
        if url in known or path is None:
            continue
        ProductImage.objects.create(
            product=product,
            image=str(Path(path).relative_to(media_root)).replace("\\", "/"),
            alt=p.name,
            sort=sort,
            source_url=url,
        )
    return product
