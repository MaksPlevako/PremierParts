from decimal import Decimal

import pytest

from apps.catalog.models import Category, Fitment, Generation, Make, PartNumber, Product
from apps.importer import loader
from apps.importer.parsers import CategoryNode, ModelLink, ParsedProduct

pytestmark = pytest.mark.django_db


def parsed(**kw):
    data = dict(
        url="https://premier-parts.com.ua/product/fara-liva-passat",
        slug="fara-liva-passat",
        name="Фара ліва передня Volkswagen Passat B7 USA 2010-2014 (561941005D)",
        sku="FP7439R1T",
        manufacturer="TYC",
        make="Volkswagen",
        model="Passat B7 USA",
        series="(2011-2014)",
        condition="Новий",
        price=Decimal("4120"),
        in_stock=True,
        description="Механічна",
        image_urls=[],
        breadcrumbs=[("Оптика", "optika"), ("Фари передні", "fary-perednie")],
    )
    data.update(kw)
    return ParsedProduct(**data)


def test_upsert_product_is_idempotent():
    first = loader.upsert_product(parsed(), images=[])
    second = loader.upsert_product(parsed(price=Decimal("3999")), images=[])

    assert first.pk == second.pk
    assert Product.objects.count() == 1
    assert Fitment.objects.count() == 1
    second.refresh_from_db()
    assert second.price == Decimal("3999")
    numbers = set(PartNumber.objects.values_list("normalized", "kind"))
    assert numbers == {("FP7439R1T", "sku"), ("561941005D", "oem")}


def test_upsert_product_builds_car_and_category_tree():
    product = loader.upsert_product(parsed(), images=[])

    gen = product.fitments.get().generation
    assert gen.full_label == "Volkswagen Passat B7 USA (2011–2014)"
    assert gen.model.market == "usa"
    assert product.category.slug == "fary-perednie"
    assert product.category.parent.slug == "optika"
    assert (product.side, product.position) == ("left", "front")
    assert product.stock_status == "in_stock"


def test_out_of_stock_product_becomes_on_order():
    product = loader.upsert_product(parsed(in_stock=False, price=Decimal("0")), images=[])
    assert product.stock_status == "on_order"


def test_upsert_generation_uses_legacy_ids_and_years():
    make = loader.upsert_make(544, "Hyundai")
    link = ModelLink(544, 25775, 24560, "Accent", (2011, 2018))

    gen = loader.upsert_generation(make, link)
    again = loader.upsert_generation(make, link)

    assert gen.pk == again.pk
    assert gen.legacy_id == "25775:24560"
    assert (gen.year_from, gen.year_to, gen.slug) == (2011, 2018, "2011-2018")
    assert gen.model.legacy_id == 25775


def test_generation_from_product_matches_existing_legacy_generation():
    make = loader.upsert_make(574, "Volkswagen")
    legacy_gen = loader.upsert_generation(make, ModelLink(574, 25714, 24676, "Passat B7 USA", (2011, 2014)))

    product = loader.upsert_product(parsed(), images=[])

    assert product.fitments.get().generation_id == legacy_gen.id
    assert Generation.objects.count() == 1


def test_make_alias_merges_typos():
    porsche = loader.upsert_make(24893, "Porsche")
    typo = loader.upsert_make(4705, "Porshe")
    assert porsche.pk == typo.pk
    assert Make.objects.filter(name__icontains="pors").count() == 1


def test_category_tree_from_home_menu():
    nodes = [
        CategoryNode("Оптика", None, None, [CategoryNode("Фари передні", "fary-perednie")]),
        CategoryNode("Кузов", None, None, [CategoryNode("Двері", "dveri")]),
    ]
    loader.upsert_category_tree(nodes)

    optics = Category.objects.get(name="Оптика")
    assert optics.icon == "light"
    assert Category.objects.get(slug="fary-perednie").parent == optics
    assert Category.objects.get(slug="dveri").parent.name == "Кузов"

    # a product breadcrumb later reveals the legacy slug of the parent
    loader.ensure_category_path([("Оптика", "optika"), ("Фари передні", "fary-perednie")])
    optics.refresh_from_db()
    assert optics.slug == "optika"
