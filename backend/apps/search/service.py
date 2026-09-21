"""Catalog listings and search: one query model, Meilisearch first, Postgres as a fallback."""

import logging
import math
from dataclasses import dataclass, field, replace

from django.db.models import Count, Q

from apps.catalog.models import CarModel, Category, Generation, Make, Manufacturer, PartNumber, Product
from apps.catalog.services.pricing import live_promotions
from apps.catalog.services.queries import car_ref, card_queryset, cards_by_ids, product_cards
from apps.content.models import Promotion
from apps.core.normalize import normalize_part_number

from . import index
from .understanding import Understood, understand

log = logging.getLogger(__name__)

SORTS = {"popular", "price_asc", "price_desc", "new"}
REFINE_FIELDS = {"manufacturer_id", "side", "stock_status", "price"}


@dataclass(frozen=True)
class Clause:
    field: str
    op: str  # "=", "in", ">=", "<="
    value: object

    def meili(self) -> str:
        if self.op == "in":
            return f"{self.field} IN [{', '.join(str(int(v)) for v in self.value)}]"
        if isinstance(self.value, str):
            return f'{self.field} {self.op} "{self.value}"'
        return f"{self.field} {self.op} {self.value}"

    def django(self) -> Q:
        f, v = self.field, self.value
        if f == "category_ids":
            return Q(category_id=v) | Q(category__parent_id=v)
        if f == "make_ids":
            return Q(fitments__generation__model__make_id=v)
        if f == "model_ids":
            return Q(fitments__generation__model_id__in=v)
        if f == "generation_ids":
            return Q(fitments__generation_id__in=v)
        if f == "manufacturer_id":
            return Q(manufacturer_id__in=v)
        if f == "promotion_ids":
            from apps.catalog.views import promotion_products_q

            promo = Promotion.objects.filter(id=v).first()
            return promotion_products_q(promo) if promo else Q(pk__in=[])
        if f == "price":
            return Q(price__gte=v) if self.op == ">=" else Q(price__lte=v)
        return Q(**{f: v})


@dataclass
class ListingParams:
    q: str = ""
    category_slug: str | None = None
    make_slug: str | None = None
    model_slug: str | None = None
    generation_id: int | None = None
    car_generation_id: int | None = None
    all_cars: bool = False
    manufacturer_ids: list[int] = field(default_factory=list)
    side: str | None = None
    stock: str | None = None
    price_min: float | None = None
    price_max: float | None = None
    promo_slug: str | None = None
    sort: str = "popular"
    page: int = 1
    page_size: int = 24

    @classmethod
    def from_query(cls, qp) -> "ListingParams":
        def to_int(name):
            try:
                return int(qp.get(name)) if qp.get(name) not in (None, "") else None
            except (TypeError, ValueError):
                return None

        def to_float(name):
            try:
                return float(qp.get(name)) if qp.get(name) not in (None, "") else None
            except (TypeError, ValueError):
                return None

        manufacturers = []
        for raw in qp.getlist("manufacturer") if hasattr(qp, "getlist") else []:
            for part in str(raw).split(","):
                if part.strip().isdigit():
                    manufacturers.append(int(part))
        sort = qp.get("sort") or "popular"
        return cls(
            q=(qp.get("q") or "").strip()[:200],
            category_slug=qp.get("category") or None,
            make_slug=qp.get("make") or None,
            model_slug=qp.get("model") or None,
            generation_id=to_int("generation"),
            car_generation_id=to_int("car"),
            all_cars=qp.get("all_cars") in ("1", "true"),
            manufacturer_ids=manufacturers,
            side=qp.get("side") if qp.get("side") in ("left", "right") else None,
            stock=qp.get("stock") if qp.get("stock") in ("in_stock", "on_order") else None,
            price_min=to_float("price_min"),
            price_max=to_float("price_max"),
            promo_slug=qp.get("promo") or None,
            sort=sort if sort in SORTS else "popular",
            page=max(1, min(to_int("page") or 1, 200)),
            page_size=max(1, min(to_int("page_size") or 24, 60)),
        )


def _category_id(slug):
    return Category.objects.filter(slug=slug, is_active=True).values_list("id", flat=True).first()


def _car_clauses(params: ListingParams, u: Understood | None) -> tuple[list[Clause], str | None, dict | None]:
    """Which car filter applies: explicit page car > car typed in the query > «Моє авто»."""
    if params.generation_id:
        gen = Generation.objects.select_related("model__make").filter(id=params.generation_id).first()
        return [Clause("generation_ids", "in", [params.generation_id])], "page", car_ref(gen) if gen else None
    if params.model_slug and params.make_slug:
        model = CarModel.objects.select_related("make").filter(make__slug=params.make_slug, slug=params.model_slug).first()
        if model:
            return [Clause("model_ids", "in", [model.id])], "page", {"make": model.make.name, "label": model.name}
    if params.make_slug:
        make = Make.objects.filter(slug=params.make_slug).first()
        if make:
            return [Clause("make_ids", "=", make.id)], "page", {"make": make.name, "label": make.name}
    if u and (u.generation_ids or u.model_ids or u.make_id):
        if u.generation_ids:
            clauses = [Clause("generation_ids", "in", u.generation_ids)]
        elif u.model_ids:
            clauses = [Clause("model_ids", "in", u.model_ids)]
        else:
            clauses = [Clause("make_ids", "=", u.make_id)]
        return clauses, "query", understood_car(u)
    if params.car_generation_id and not params.all_cars:
        gen = Generation.objects.select_related("model__make").filter(id=params.car_generation_id).first()
        if gen:
            return [Clause("generation_ids", "in", [gen.id])], "my_car", car_ref(gen)
    return [], None, None


def understood_car(u: Understood) -> dict | None:
    if u.generation_ids and len(u.generation_ids) == 1:
        gen = Generation.objects.select_related("model__make").get(id=u.generation_ids[0])
        return car_ref(gen)
    if u.model_ids:
        models = list(CarModel.objects.select_related("make").filter(id__in=u.model_ids))
        make = models[0].make
        label = _common_label([m.name for m in models]) or " / ".join(sorted({m.family or m.name for m in models}))
        return {
            "make": make.name,
            "make_slug": make.slug,
            "label": label,
            "full_label": f"{make.name} {label}" + (f" {u.year}" if u.year else ""),
            "model_slug": models[0].slug if len(models) == 1 else None,
            "models": [{"id": m.id, "name": m.name, "slug": m.slug} for m in models],
        }
    if u.make_id:
        make = Make.objects.get(id=u.make_id)
        return {"make": make.name, "make_slug": make.slug, "label": make.name, "full_label": make.name, "models": []}
    return None


def _common_label(names: list[str]) -> str:
    """Longest common word prefix: ['Passat B7', 'Passat B7 USA'] -> 'Passat B7'."""
    split = [n.split() for n in names]
    common = []
    for words in zip(*split):
        if len({w.lower() for w in words}) != 1:
            break
        common.append(words[0])
    return " ".join(common)


def understood_payload(u: Understood | None) -> dict | None:
    if not u:
        return None
    category = None
    if u.category_id:
        cat = Category.objects.filter(id=u.category_id).first()
        category = {"id": cat.id, "slug": cat.slug, "name": cat.name} if cat else None
    return {
        "kind": u.kind,
        "text": u.text,
        "part_number": u.part_number,
        "vin": u.vin,
        "category": category,
        "car": understood_car(u),
        "side": u.side,
        "position": u.position,
        "year": u.year,
    }


def _sort(params: ListingParams, has_text: bool) -> list[str] | None:
    if params.sort == "price_asc":
        return ["has_price:desc", "price:asc"]
    if params.sort == "price_desc":
        return ["price:desc"]
    if params.sort == "new":
        return ["created_at:desc"]
    return None if has_text else ["has_price:desc", "popularity:desc"]


def _refine_clauses(params: ListingParams) -> list[Clause]:
    clauses = []
    if params.manufacturer_ids:
        clauses.append(Clause("manufacturer_id", "in", params.manufacturer_ids))
    if params.side:
        clauses.append(Clause("side", "=", params.side))
    if params.stock:
        clauses.append(Clause("stock_status", "=", params.stock))
    if params.price_min is not None:
        clauses.append(Clause("price", ">=", params.price_min))
    if params.price_max is not None:
        clauses.append(Clause("price", "<=", params.price_max))
    return clauses


def _category_facets(distribution: dict, parent_slug: str | None) -> list[dict]:
    counts = {int(k): v for k, v in (distribution or {}).items()}
    if not counts:
        return []
    qs = Category.objects.filter(id__in=counts.keys(), is_active=True)
    if parent_slug:
        qs = qs.filter(parent__slug=parent_slug)
    else:
        qs = qs.filter(parent__isnull=False)
    items = [{"id": c.id, "slug": c.slug, "name": c.name, "count": counts[c.id]} for c in qs]
    return sorted(items, key=lambda x: -x["count"])[:16]


def _manufacturer_facets(distribution: dict) -> list[dict]:
    counts = {int(k): v for k, v in (distribution or {}).items()}
    names = dict(Manufacturer.objects.filter(id__in=counts).values_list("id", "name"))
    return sorted(
        ({"id": i, "name": names.get(i, "—"), "count": n} for i, n in counts.items() if i in names),
        key=lambda x: (-x["count"], x["name"]),
    )


@dataclass
class _Plan:
    text: str
    structural: list[Clause]
    car: list[Clause]
    semantic: list[Clause]  # category / side / position derived from the query text
    refine: list[Clause]

    def all(self, *, skip_fields: set[str] = frozenset()) -> list[Clause]:
        return [c for c in self.structural + self.car + self.semantic + self.refine if c.field not in skip_fields]


def _meili_run(plan: _Plan, params: ListingParams, category_parent: str | None, extra: dict) -> dict:
    sort = _sort(params, bool(plan.text))
    main = {
        "q": plan.text,
        "filter": [c.meili() for c in plan.all()],
        "facets": ["category_ids"],
        "page": params.page,
        "hitsPerPage": params.page_size,
        "attributesToRetrieve": ["id"],
        **extra,
    }
    if sort:
        main["sort"] = sort
    manufacturers = {
        "q": plan.text,
        "filter": [c.meili() for c in plan.all(skip_fields={"manufacturer_id"})],
        "facets": ["manufacturer_id"],
        "hitsPerPage": 0,
        **extra,
    }
    others = {
        "q": plan.text,
        "filter": [c.meili() for c in plan.all(skip_fields={"side", "stock_status", "price"})],
        "facets": ["side", "stock_status", "price"],
        "hitsPerPage": 0,
        **extra,
    }
    res_main, res_man, res_other = index.multi_search([main, manufacturers, others])
    stats = (res_other.get("facetStats") or {}).get("price") or {}
    side = res_other.get("facetDistribution", {}).get("side", {})
    stock = res_other.get("facetDistribution", {}).get("stock_status", {})
    return {
        "ids": [h["id"] for h in res_main["hits"]],
        "count": res_main.get("totalHits", 0),
        "facets": {
            "categories": _category_facets(res_main.get("facetDistribution", {}).get("category_ids"), category_parent),
            "manufacturers": _manufacturer_facets(res_man.get("facetDistribution", {}).get("manufacturer_id")),
            "side": {"left": side.get("left", 0), "right": side.get("right", 0)},
            "stock": {"in_stock": stock.get("in_stock", 0), "on_order": stock.get("on_order", 0)},
        },
        "price_range": {"min": stats.get("min", 0), "max": stats.get("max", 0)},
    }


def _pg_run(plan: _Plan, params: ListingParams, category_parent: str | None) -> dict:
    qs = Product.objects.filter(is_active=True)
    for clause in plan.all():
        qs = qs.filter(clause.django())
    for token in plan.text.split():
        normalized = normalize_part_number(token)
        cond = Q(name__icontains=token) | Q(sku__icontains=token)
        if normalized:
            cond |= Q(part_numbers__normalized__startswith=normalized)
        qs = qs.filter(cond)
    qs = qs.distinct()
    order = {
        "price_asc": ["price"],
        "price_desc": ["-price"],
        "new": ["-created_at"],
    }.get(params.sort, ["-popularity"])
    ids = list(qs.order_by(*order).values_list("id", flat=True))
    start = (params.page - 1) * params.page_size
    cat_rows = qs.order_by().values("category_id").annotate(n=Count("id"))
    man_rows = qs.order_by().values("manufacturer_id").annotate(n=Count("id"))
    return {
        "ids": ids[start : start + params.page_size],
        "count": len(ids),
        "facets": {
            "categories": _category_facets({r["category_id"]: r["n"] for r in cat_rows}, category_parent),
            "manufacturers": _manufacturer_facets({r["manufacturer_id"]: r["n"] for r in man_rows if r["manufacturer_id"]}),
            "side": {"left": qs.filter(side="left").count(), "right": qs.filter(side="right").count()},
            "stock": {"in_stock": qs.filter(stock_status="in_stock").count(), "on_order": qs.filter(stock_status="on_order").count()},
        },
        "price_range": {"min": 0, "max": 0},
    }


def _run(plan: _Plan, params: ListingParams, category_parent: str | None, extra: dict | None = None) -> tuple[dict, bool]:
    try:
        return _meili_run(plan, params, category_parent, extra or {}), False
    except Exception as exc:
        log.warning("meilisearch unavailable, falling back to postgres: %s", exc)
        return _pg_run(plan, params, category_parent), True


def _vin_plan(u: Understood) -> tuple[list[Clause], dict | None, dict | None]:
    try:
        from apps.vin.service import decode_and_match

        decoded = decode_and_match(u.vin)
    except Exception as exc:
        log.warning("vin decode failed: %s", exc)
        return [], None, None
    matches = decoded.get("matches") or []
    if not matches:
        return [], None, decoded
    return [Clause("generation_ids", "in", [m["generation_id"] for m in matches])], matches[0], decoded


def query_products(params: ListingParams) -> dict:
    u = understand(params.q) if params.q else None
    structural: list[Clause] = []
    category_parent = None
    if params.category_slug:
        cat_id = _category_id(params.category_slug)
        structural.append(Clause("category_ids", "=", cat_id or 0))
        category_parent = params.category_slug
    if params.promo_slug:
        promo = Promotion.objects.live().filter(slug=params.promo_slug).first()
        structural.append(Clause("promotion_ids", "=", promo.id if promo else 0))

    car_clauses, car_source, car = _car_clauses(params, u)
    vin = None
    text = ""
    semantic: list[Clause] = []
    exact_ids: list[int] = []
    if u:
        if u.kind == "vin":
            vin_clauses, vin_car, vin = _vin_plan(u)
            if vin_clauses:
                car_clauses, car_source, car = vin_clauses, "vin", vin_car
            else:
                text = u.vin
        elif u.kind == "part_number":
            text = u.part_number
            exact_ids = list(
                PartNumber.objects.filter(normalized=u.part_number, product__is_active=True)
                .values_list("product_id", flat=True)
                .distinct()
            )
        else:
            text = u.text
            if u.category_id and not params.category_slug:
                semantic.append(Clause("category_ids", "=", u.category_id))
            if u.side and not params.side:
                semantic.append(Clause("side", "=", u.side))
            if u.position:
                semantic.append(Clause("position", "=", u.position))

    plan = _Plan(text=text, structural=structural, car=car_clauses, semantic=semantic, refine=_refine_clauses(params))
    result, degraded = _run(plan, params, category_parent)
    relaxed = False
    if result["count"] == 0 and u and u.kind == "text" and (plan.semantic or car_source == "query"):
        # 1) drop side/position; 2) plain text search over names (they often list several cars);
        # 3) keep only the car
        attempts = [
            (replace(plan, semantic=[c for c in plan.semantic if c.field == "category_ids"]), {}),
            (replace(plan, semantic=[], car=[] if car_source == "query" else plan.car, text=u.raw), {"matchingStrategy": "all"}),
            (replace(plan, semantic=[]), {}),
        ]
        for relaxed_plan, extra in attempts:
            result, degraded = _run(relaxed_plan, params, category_parent, extra)
            if result["count"]:
                relaxed = True
                if not relaxed_plan.car:
                    car_source, car = None, None
                break
    if result["count"] == 0 and u and u.kind == "part_number" and not exact_ids:
        # the number may be a fragment of a longer one — try prefix search on the raw text
        result, degraded = _run(replace(plan, text=u.raw), params, category_parent)

    ids = result["ids"]
    if exact_ids and params.page == 1:
        ids = exact_ids + [i for i in ids if i not in exact_ids]
        ids = ids[: params.page_size]
        result["count"] = max(result["count"], len(set(exact_ids) | set(result["ids"])))
    promos = live_promotions()
    cards = cards_by_ids(ids, promos)
    for card in cards:
        card["exact"] = card["id"] in exact_ids
    return {
        "count": result["count"],
        "page": params.page,
        "page_size": params.page_size,
        "pages": max(1, math.ceil(result["count"] / params.page_size)),
        "results": cards,
        "facets": result["facets"],
        "price_range": result["price_range"],
        "understood": understood_payload(u),
        "vin": vin,
        "car": car,
        "car_source": car_source,
        "relaxed": relaxed,
        "degraded": degraded,
    }


def suggest(q: str, car_generation_id: int | None = None) -> dict:
    u = understand(q)
    if u.kind == "empty":
        return {"kind": "empty", "products": [], "categories": [], "total": 0}
    if u.kind == "vin":
        try:
            from apps.vin.service import decode_and_match

            decoded = decode_and_match(u.vin)
        except Exception as exc:
            log.warning("vin decode failed: %s", exc)
            decoded = {"vin": u.vin, "valid": False, "matches": [], "error": str(exc)}
        matches = decoded.get("matches") or []
        categories, total = [], 0
        if matches:
            gen_ids = [m["generation_id"] for m in matches[:1]]
            rows = (
                Product.objects.filter(is_active=True, fitments__generation_id__in=gen_ids)
                .values("category_id", "category__slug", "category__name")
                .annotate(count=Count("id", distinct=True))
                .order_by("-count")
            )
            categories = [{"id": r["category_id"], "slug": r["category__slug"], "name": r["category__name"], "count": r["count"]} for r in rows]
            total = Product.objects.filter(is_active=True, fitments__generation_id__in=gen_ids).distinct().count()
        return {
            "kind": "vin",
            "vin": decoded,
            "car": matches[0] if matches else None,
            "products": [],
            "categories": categories[:8],
            "total": total,
        }

    listing = query_products(ListingParams(q=q, car_generation_id=car_generation_id, page_size=6))
    products = listing["results"]
    analogs: list[dict] = []
    if u.kind == "part_number":
        exact = [p for p in products if p.get("exact")]
        if exact:
            numbers = PartNumber.objects.filter(product_id__in=[p["id"] for p in exact]).exclude(kind="sku").values_list("normalized", flat=True)
            analog_ids = list(
                PartNumber.objects.filter(normalized__in=list(numbers), product__is_active=True)
                .exclude(product_id__in=[p["id"] for p in exact])
                .values_list("product_id", flat=True)
                .distinct()[:4]
            )
            analogs = product_cards(card_queryset().filter(id__in=analog_ids))
            products = exact + [p for p in products if not p.get("exact") and p["id"] not in analog_ids][: max(0, 6 - len(exact) - len(analogs))]
    return {
        "kind": u.kind,
        "part_number": u.part_number,
        "understood": listing["understood"],
        "car": listing["car"],
        "car_source": listing["car_source"],
        "products": products,
        "analogs": analogs,
        "categories": listing["facets"]["categories"][:6],
        "total": listing["count"],
        "relaxed": listing["relaxed"],
        "degraded": listing["degraded"],
    }
