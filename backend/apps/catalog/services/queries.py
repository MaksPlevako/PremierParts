"""Read-side helpers: product cards, category tree with counts, car references."""

from collections import defaultdict

from django.db.models import Count, Prefetch, Q, QuerySet

from ..models import Category, Generation, Make, Product, ProductImage
from .pricing import ActivePromotion, effective_price, live_promotions


def card_queryset() -> QuerySet[Product]:
    return (
        Product.objects.filter(is_active=True)
        .select_related("category__parent", "manufacturer")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("sort", "id")),
            "fitments",
        )
    )


def _num(value):
    if value is None:
        return None
    return int(value) if value == int(value) else float(value)


def first_image_url(product: Product) -> str | None:
    image = next(iter(product.images.all()), None)
    return image.image.url if image and image.image else None


def price_fields(product: Product, promos: list[ActivePromotion]) -> dict:
    info = effective_price(product, promos)
    return {
        "price": _num(info.price),
        "sale_price": _num(info.sale_price),
        "old_price": _num(info.old_price),
        "discount_percent": info.discount_percent,
        "promotion_id": info.promotion_id,
    }


def serialize_card(product: Product, promos: list[ActivePromotion]) -> dict:
    return {
        "id": product.id,
        "slug": product.slug,
        "name": product.name,
        "sku": product.sku,
        "manufacturer": product.manufacturer.name if product.manufacturer_id else None,
        "image": first_image_url(product),
        **price_fields(product, promos),
        "stock_status": product.stock_status,
        "generation_ids": sorted(f.generation_id for f in product.fitments.all()),
        "category": {"slug": product.category.slug, "name": product.category.name},
    }


def product_cards(products, promos: list[ActivePromotion] | None = None) -> list[dict]:
    if promos is None:
        promos = live_promotions()
    return [serialize_card(p, promos) for p in products]


def cards_by_ids(ids: list[int], promos: list[ActivePromotion] | None = None) -> list[dict]:
    """Cards in the same order as ``ids`` (used for search hits)."""
    by_id = {p.id: p for p in card_queryset().filter(id__in=ids)}
    return product_cards([by_id[i] for i in ids if i in by_id], promos)


def category_counts() -> dict[int, int]:
    # .order_by() matters: modeltranslation turns Meta.ordering into an explicit ORDER BY that would leak into GROUP BY
    rows = Product.objects.filter(is_active=True).order_by().values("category_id").annotate(n=Count("id"))
    direct = {row["category_id"]: row["n"] for row in rows}
    totals: dict[int, int] = defaultdict(int)
    for cat in Category.objects.only("id", "parent_id"):
        n = direct.get(cat.id, 0)
        totals[cat.id] += n
        if cat.parent_id:
            totals[cat.parent_id] += n
    return totals


def category_node(cat: Category, counts: dict[int, int], children: list[Category] | None = None) -> dict:
    return {
        "id": cat.id,
        "slug": cat.slug,
        "name": cat.name,
        "icon": cat.icon,
        "image": cat.image.url if cat.image else None,
        "product_count": counts.get(cat.id, 0),
        "children": [category_node(c, counts, []) for c in (children or [])],
    }


def category_tree() -> list[dict]:
    counts = category_counts()
    cats = list(Category.objects.filter(is_active=True).order_by("sort", "name"))
    children: dict[int, list[Category]] = defaultdict(list)
    for c in cats:
        if c.parent_id:
            children[c.parent_id].append(c)
    return [category_node(c, counts, children[c.id]) for c in cats if c.parent_id is None]


def car_ref(gen: Generation) -> dict:
    model = gen.model
    return {
        "generation_id": gen.id,
        "make": model.make.name,
        "make_slug": model.make.slug,
        "model": model.name,
        "model_slug": model.slug,
        "generation_slug": gen.slug,
        "label": gen.label,
        "full_label": gen.full_label,
        "years_label": gen.years_label,
        "market": model.market,
    }


def makes_with_counts() -> list[dict]:
    makes = Make.objects.annotate(
        n=Count(
            "models__generations__fitments__product",
            filter=Q(models__generations__fitments__product__is_active=True),
            distinct=True,
        )
    ).order_by("sort", "name")
    return [
        {
            "id": m.id,
            "name": m.name,
            "slug": m.slug,
            "logo": m.logo.url if m.logo else None,
            "is_popular": m.is_popular,
            "product_count": m.n,
        }
        for m in makes
    ]


def generation_product_counts(generation_ids) -> dict[int, int]:
    rows = (
        Product.objects.filter(is_active=True, fitments__generation_id__in=generation_ids)
        .order_by()
        .values("fitments__generation_id")
        .annotate(n=Count("id", distinct=True))
    )
    return {r["fitments__generation_id"]: r["n"] for r in rows}
