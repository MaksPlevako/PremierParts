"""Tiny object factories for tests (no external factory library needed)."""

from datetime import timedelta
from decimal import Decimal
from itertools import count

from django.utils import timezone

from apps.catalog.models import (
    CarModel,
    Category,
    Fitment,
    Generation,
    Make,
    Manufacturer,
    PartNumber,
    Product,
)
from apps.content.models import Promotion

_seq = count(1)


def make_make(name="Volkswagen", **kw):
    return Make.objects.get_or_create(name=name, defaults={"slug": name.lower().replace(" ", "-"), **kw})[0]


def make_generation(make="Volkswagen", model="Passat B7 USA", year_from=2011, year_to=2014, **kw):
    mk = make_make(make)
    model_obj = CarModel.objects.get_or_create(
        make=mk, name=model, defaults={"slug": model.lower().replace(" ", "-")}
    )[0]
    slug = f"{year_from or ''}-{year_to or ''}".strip("-") or "all"
    return Generation.objects.get_or_create(
        model=model_obj, slug=slug, defaults={"year_from": year_from, "year_to": year_to, **kw}
    )[0]


def make_category(name="Фари передні", slug="fary-perednie", parent=None, **kw):
    return Category.objects.get_or_create(slug=slug, defaults={"name": name, "parent": parent, **kw})[0]


def make_manufacturer(name="TYC"):
    return Manufacturer.objects.get_or_create(name=name, defaults={"slug": name.lower()})[0]


def make_product(name=None, price="3438", category=None, generations=(), numbers=(), **kw):
    n = next(_seq)
    if category is None:
        parent = make_category("Оптика", "optika")
        category = make_category(parent=parent)
    product = Product.objects.create(
        name=name or f"Фара ліва передня #{n}",
        slug=kw.pop("slug", f"product-{n}"),
        category=category,
        price=Decimal(price),
        manufacturer=kw.pop("manufacturer", make_manufacturer()),
        sku=kw.pop("sku", f"SKU{n:05d}"),
        **kw,
    )
    for gen in generations:
        Fitment.objects.create(product=product, generation=gen)
    for number in numbers:
        PartNumber.objects.create(product=product, number=number, kind="oem")
    return product


def make_promotion(percent=15, **kw):
    now = timezone.now()
    n = next(_seq)
    return Promotion.objects.create(
        title=kw.pop("title", f"Акція {n}"),
        slug=kw.pop("slug", f"promo-{n}"),
        discount_percent=percent,
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=7),
        **kw,
    )
