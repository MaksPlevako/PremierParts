from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.catalog.models import Category, Manufacturer, Product
from apps.catalog.services.pricing import effective_price, live_promotions
from apps.content.models import Promotion


@pytest.fixture
def optics(db):
    parent = Category.objects.create(name="Оптика", slug="optika")
    return Category.objects.create(name="Фари передні", slug="fary-perednie", parent=parent)


@pytest.fixture
def headlight(optics):
    tyc = Manufacturer.objects.create(name="TYC", slug="tyc")
    return Product.objects.create(name="Фара", slug="fara", category=optics, manufacturer=tyc, price=Decimal("3438"))


def _promo(percent, **kw):
    now = timezone.now()
    return Promotion.objects.create(
        title=f"-{percent}%", slug=f"p{percent}", discount_percent=percent,
        starts_at=kw.pop("starts_at", now - timedelta(days=1)), ends_at=kw.pop("ends_at", now + timedelta(days=1)), **kw
    )


@pytest.mark.django_db
def test_no_promotions_means_plain_price(headlight):
    info = effective_price(headlight, [])
    assert info.price == Decimal("3438")
    assert info.sale_price is None
    assert info.discount_percent is None


@pytest.mark.django_db
def test_category_promotion_applies_to_child_category(headlight):
    promo = _promo(15)
    promo.categories.add(headlight.category.parent)

    info = effective_price(headlight, live_promotions())

    assert info.sale_price == Decimal("2922")
    assert info.old_price == Decimal("3438")
    assert info.discount_percent == 15
    assert info.promotion_id == promo.id


@pytest.mark.django_db
def test_biggest_discount_wins(headlight):
    _promo(10).manufacturers.add(headlight.manufacturer)
    _promo(20).products.add(headlight)

    assert effective_price(headlight, live_promotions()).discount_percent == 20


@pytest.mark.django_db
def test_zero_price_never_discounted(headlight):
    headlight.price = Decimal("0")
    _promo(15).products.add(headlight)

    info = effective_price(headlight, live_promotions())
    assert info.sale_price is None and info.discount_percent is None


@pytest.mark.django_db
def test_expired_promotion_ignored(headlight):
    now = timezone.now()
    _promo(30, starts_at=now - timedelta(days=10), ends_at=now - timedelta(days=1)).products.add(headlight)

    assert live_promotions() == []
    assert effective_price(headlight, live_promotions()).sale_price is None


@pytest.mark.django_db
def test_old_price_without_promotion_shows_discount(headlight):
    headlight.old_price = Decimal("4000")

    info = effective_price(headlight, [])
    assert info.old_price == Decimal("4000")
    assert info.discount_percent == 14
    assert info.sale_price is None
