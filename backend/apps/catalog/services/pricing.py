"""Effective price of a product: plain price, manual old price, or the best live promotion."""

from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal

from apps.content.models import Promotion

from .category_hierarchy import category_and_descendant_ids, category_children


@dataclass(frozen=True)
class ActivePromotion:
    id: int
    slug: str
    title: str
    percent: int
    product_ids: frozenset[int]
    category_ids: frozenset[int]
    manufacturer_ids: frozenset[int]

    def applies_to(self, product) -> bool:
        if product.id in self.product_ids:
            return True
        if product.manufacturer_id and product.manufacturer_id in self.manufacturer_ids:
            return True
        if product.category_id in self.category_ids:
            return True
        return False


@dataclass(frozen=True)
class PriceInfo:
    price: Decimal
    sale_price: Decimal | None = None
    old_price: Decimal | None = None
    discount_percent: int | None = None
    promotion_id: int | None = None

    @property
    def final(self) -> Decimal:
        return self.sale_price if self.sale_price is not None else self.price


def live_promotions() -> list[ActivePromotion]:
    promos = list(
        Promotion.objects.live()
        .filter(discount_percent__gt=0)
        .prefetch_related("products", "categories", "manufacturers")
    )
    categories_by_promo = {p.id: [category.id for category in p.categories.all()] for p in promos}
    children = category_children() if any(categories_by_promo.values()) else {}
    return [
        ActivePromotion(
            id=p.id,
            slug=p.slug,
            title=p.title,
            percent=p.discount_percent,
            product_ids=frozenset(x.id for x in p.products.all()),
            category_ids=frozenset(category_and_descendant_ids(categories_by_promo[p.id], children=children)),
            manufacturer_ids=frozenset(x.id for x in p.manufacturers.all()),
        )
        for p in promos
    ]


def best_promotion(product, promos: list[ActivePromotion]) -> ActivePromotion | None:
    applicable = [p for p in promos if p.applies_to(product)]
    return max(applicable, key=lambda p: p.percent, default=None)


def effective_price(product, promos: list[ActivePromotion] | None = None) -> PriceInfo:
    if promos is None:
        promos = live_promotions()
    price = Decimal(product.price or 0)
    if price <= 0:
        return PriceInfo(price=Decimal("0"))

    promo = best_promotion(product, promos)
    if promo:
        sale = (price * (100 - promo.percent) / 100).quantize(Decimal("1"), rounding=ROUND_DOWN)
        return PriceInfo(price=price, sale_price=sale, old_price=price, discount_percent=promo.percent, promotion_id=promo.id)

    old = Decimal(product.old_price) if product.old_price else None
    if old and old > price:
        percent = int(((old - price) / old * 100).to_integral_value(rounding=ROUND_DOWN))
        return PriceInfo(price=price, old_price=old, discount_percent=percent or None)
    return PriceInfo(price=price)
