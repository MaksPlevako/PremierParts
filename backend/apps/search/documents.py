"""Product -> Meilisearch document."""

from django.db.models import Prefetch

from apps.catalog.models import Fitment, Product, ProductImage
from apps.catalog.services.pricing import ActivePromotion, effective_price
from apps.core.normalize import normalize_part_number


def load_products(ids=None):
    qs = (
        Product.objects.filter(is_active=True)
        .select_related("category__parent", "manufacturer")
        .prefetch_related(
            "part_numbers",
            Prefetch("images", queryset=ProductImage.objects.order_by("sort", "id")),
            Prefetch("fitments", queryset=Fitment.objects.select_related("generation__model__make")),
        )
        .order_by("id")
    )
    if ids is not None:
        qs = qs.filter(id__in=ids)
    return qs


def _unique(values):
    return list(dict.fromkeys(v for v in values if v not in (None, "")))


def product_document(p: Product, promos: list[ActivePromotion], categories=None) -> dict:
    info = effective_price(p, promos)
    gens = [f.generation for f in p.fitments.all()]
    numbers = [normalize_part_number(p.sku), p.sku] if p.sku else []
    for pn in p.part_numbers.all():
        numbers.extend([pn.normalized, pn.number])
    category_ids = []
    category_names = []
    if categories is None:
        category = p.category
        while category and category.id not in category_ids:
            category_ids.append(category.id)
            category_names.append(category.name)
            category = category.parent
    else:
        category_id = p.category_id
        while category_id and category_id not in category_ids and category_id in categories:
            parent_id, name = categories[category_id]
            category_ids.append(category_id)
            category_names.append(name)
            category_id = parent_id
    image = next(iter(p.images.all()), None)
    final = info.final
    return {
        "id": p.id,
        "slug": p.slug,
        "name": p.name,
        "sku": p.sku,
        "part_numbers": _unique(numbers),
        "manufacturer": p.manufacturer.name if p.manufacturer_id else None,
        "manufacturer_id": p.manufacturer_id,
        "category": " / ".join(category_names),
        "category_ids": category_ids,
        "make": _unique(g.model.make.name for g in gens),
        "make_ids": _unique(g.model.make_id for g in gens),
        "model": _unique(g.model.name for g in gens),
        "family": _unique(g.model.family for g in gens),
        "model_ids": _unique(g.model_id for g in gens),
        "generation": _unique(g.label for g in gens),
        "generation_ids": _unique(g.id for g in gens),
        "side": p.side,
        "position": p.position,
        "stock_status": p.stock_status,
        "price": int(final) if final == int(final) else float(final),
        "has_price": final > 0,
        "promo": info.promotion_id is not None,
        "promotion_ids": [info.promotion_id] if info.promotion_id else [],
        "popularity": p.popularity,
        "created_at": int(p.created_at.timestamp()),
        "image": image.image.url if image and image.image else None,
    }
