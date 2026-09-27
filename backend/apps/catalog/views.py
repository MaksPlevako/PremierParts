import re
from collections import OrderedDict

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.content.models import Banner, Promotion
from apps.content.serializers import banner_data, promotion_data

from .models import CarModel, Category, Generation, Make, Product, StockStatus
from .services.pricing import live_promotions
from .services.queries import (
    car_ref,
    card_queryset,
    category_counts,
    category_node,
    category_tree,
    generation_product_counts,
    makes_with_counts,
    product_cards,
    serialize_card,
)


@api_view(["GET"])
def home(request):
    promos = live_promotions()
    featured = card_queryset().filter(is_featured=True).order_by("-popularity")[:12]
    if not featured:
        featured = card_queryset().filter(price__gt=0, stock_status=StockStatus.IN_STOCK)[:12]
    banners = {
        placement: [banner_data(b) for b in Banner.objects.live().filter(placement=placement)]
        for placement in (Banner.Placement.HERO, Banner.Placement.BENTO, Banner.Placement.HOME_STRIP)
    }
    makes = [m for m in makes_with_counts() if m["is_popular"]][:16]
    return Response(
        {
            "banners": banners,
            "categories": category_tree(),
            "featured": product_cards(featured, promos),
            "popular_makes": makes,
            "promotions": [promotion_data(p) for p in Promotion.objects.live()[:6]],
            "stats": {
                "products": Product.objects.filter(is_active=True).count(),
                "makes": Make.objects.count(),
            },
        }
    )


@api_view(["GET"])
def categories(request):
    return Response(category_tree())


@api_view(["GET"])
def sitemap_index(request):
    """Small, unpaginated index of public catalogue URLs for the frontend sitemap."""
    products = Product.objects.filter(is_active=True).order_by("id").values_list("slug", "updated_at")
    cars = (
        Generation.objects.filter(fitments__product__is_active=True)
        .order_by()
        .values_list("model__make__slug", "model__slug", "slug")
        .distinct()
    )
    return Response(
        {
            "products": [{"slug": slug, "updated_at": updated_at} for slug, updated_at in products],
            "cars": list(cars),
        }
    )


@api_view(["GET"])
def category_detail(request, slug):
    cat = get_object_or_404(Category.objects.select_related("parent"), slug=slug, is_active=True)
    counts = category_counts()
    data = category_node(cat, counts, list(cat.children.filter(is_active=True)))
    data["description"] = cat.description
    data["parent"] = {"slug": cat.parent.slug, "name": cat.parent.name} if cat.parent_id else None
    return Response(data)


def _related(product: Product, limit: int = 8):
    gen_ids = [f.generation_id for f in product.fitments.all()]
    base = card_queryset().exclude(id=product.id)
    related = list(base.filter(fitments__generation_id__in=gen_ids).distinct()[:limit]) if gen_ids else []
    if len(related) < limit:
        seen = {p.id for p in related}
        extra = base.filter(category_id=product.category_id).exclude(id__in=seen)[: limit - len(related)]
        related.extend(extra)
    return related


@api_view(["GET"])
def product_detail(request, slug):
    product = get_object_or_404(
        card_queryset().prefetch_related("part_numbers", "fitments__generation__model__make"), slug=slug
    )
    promos = live_promotions()
    data = serialize_card(product, promos)
    promo = next((p for p in promos if p.id == data["promotion_id"]), None)
    category = product.category
    crumbs = [{"name": "Каталог", "href": "/catalog"}]
    if category.parent_id:
        crumbs.append({"name": category.parent.name, "href": f"/category/{category.parent.slug}"})
    crumbs.append({"name": category.name, "href": f"/category/{category.slug}"})

    fitments = sorted(
        (car_ref(f.generation) for f in product.fitments.all()), key=lambda r: (r["make"], r["label"])
    )
    forma_item = getattr(product, "forma_item", None)
    attributes = (
        [{"name": row.attribute.name, "value": row.value} for row in forma_item.attributes.select_related("attribute")]
        if forma_item else []
    )
    data.update(
        {
            "description": product.description,
            "side": product.side,
            "position": product.position,
            "condition": product.condition,
            "images": [{"url": i.image.url, "alt": i.alt or product.name} for i in product.images.all() if i.image],
            "part_numbers": [{"number": pn.number, "kind": pn.kind} for pn in product.part_numbers.all()],
            "fitments": fitments,
            "attributes": attributes,
            "promotion": {"slug": promo.slug, "title": promo.title} if promo else None,
            "breadcrumbs": crumbs,
            "related": product_cards(_related(product), promos),
            "updated_at": product.updated_at.isoformat(),
        }
    )
    return Response(data)


@api_view(["GET"])
def makes(request):
    return Response(makes_with_counts())


def _generation_data(gen: Generation, counts: dict[int, int]) -> dict:
    data = {
        "id": gen.id,
        "slug": gen.slug,
        "label": gen.label,
        "years_label": gen.years_label,
        "year_from": gen.year_from,
        "year_to": gen.year_to,
        "product_count": counts.get(gen.id, 0),
    }
    if gen.source_label:
        data["type_label"] = gen.source_label
    return data


@api_view(["GET"])
def make_detail(request, slug):
    make = get_object_or_404(Make, slug=slug)
    models = list(make.models.prefetch_related("generations").order_by("family", "name"))
    gen_ids = [g.id for m in models for g in m.generations.all()]
    counts = generation_product_counts(gen_ids)
    families: "OrderedDict[str, list]" = OrderedDict()
    for model in models:
        gens = sorted(model.generations.all(), key=lambda g: (g.year_from or 0))
        families.setdefault(model.family or model.name, []).append(
            {
                "id": model.id,
                "name": model.name,
                "slug": model.slug,
                "market": model.market,
                "product_count": sum(counts.get(g.id, 0) for g in gens),
                "generations": [_generation_data(g, counts) for g in gens],
            }
        )
    return Response(
        {
            "id": make.id,
            "name": make.name,
            "slug": make.slug,
            "logo": make.logo.url if make.logo else None,
            "families": [{"family": name, "models": items} for name, items in families.items()],
        }
    )


@api_view(["GET"])
def model_detail(request, make_slug, model_slug):
    model = get_object_or_404(CarModel.objects.select_related("make"), make__slug=make_slug, slug=model_slug)
    gens = sorted(model.generations.all(), key=lambda g: (g.year_from or 0))
    counts = generation_product_counts([g.id for g in gens])
    return Response(
        {
            "id": model.id,
            "name": model.name,
            "slug": model.slug,
            "family": model.family,
            "market": model.market,
            "make": {"name": model.make.name, "slug": model.make.slug},
            "generations": [_generation_data(g, counts) for g in gens],
        }
    )


@api_view(["GET"])
def generation_detail(request, pk):
    gen = get_object_or_404(Generation.objects.select_related("model__make"), pk=pk)
    return Response(car_ref(gen))


@api_view(["GET"])
def car_detail(request, make_slug, model_slug, gen_slug):
    gen = get_object_or_404(
        Generation.objects.select_related("model__make"),
        model__make__slug=make_slug,
        model__slug=model_slug,
        slug=gen_slug,
    )
    rows = (
        Product.objects.filter(is_active=True, fitments__generation=gen)
        .order_by()
        .values("category_id", "category__slug", "category__name")
        .annotate(count=Count("id", distinct=True))
        .order_by("-count", "category__name")
    )
    data = car_ref(gen)
    data["categories"] = [
        {"id": r["category_id"], "slug": r["category__slug"], "name": r["category__name"], "count": r["count"]}
        for r in rows
    ]
    return Response(data)


_MARK = re.compile(r"^/mark/(\d+)/?$")
_MODEL = re.compile(r"^/model/(\d+)/(\d+)/(\d+)/?$")


@api_view(["GET"])
def legacy_resolve(request):
    path = request.query_params.get("path", "")
    if m := _MARK.match(path):
        make = Make.objects.filter(legacy_id=int(m.group(1))).first()
        if make:
            return Response({"location": f"/cars/{make.slug}"})
    elif m := _MODEL.match(path):
        mark_id, model_id, series_id = m.groups()
        gen = (
            Generation.objects.select_related("model__make")
            .filter(legacy_id=f"{model_id}:{series_id}")
            .first()
        )
        if gen:
            return Response({"location": f"/cars/{gen.model.make.slug}/{gen.model.slug}/{gen.slug}"})
        model = CarModel.objects.select_related("make").filter(legacy_id=int(model_id)).first()
        if model:
            return Response({"location": f"/cars/{model.make.slug}/{model.slug}"})
        make = Make.objects.filter(legacy_id=int(mark_id)).first()
        if make:
            return Response({"location": f"/cars/{make.slug}"})
    return Response({"detail": "not found"}, status=404)


def promotion_products_q(promo: Promotion) -> Q:
    cat_ids = list(promo.categories.values_list("id", flat=True))
    return (
        Q(id__in=promo.products.values("id"))
        | Q(category_id__in=cat_ids)
        | Q(category__parent_id__in=cat_ids)
        | Q(manufacturer_id__in=promo.manufacturers.values("id"))
    )
