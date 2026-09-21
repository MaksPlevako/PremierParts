from decimal import Decimal
from pathlib import Path

import pytest

from apps.importer import parsers

FIX = Path(__file__).parent / "fixtures" / "premier"
PRODUCT_URL = "https://premier-parts.com.ua/product/fara-liva-perednya-volkswagen-passat-b7-usa-2010-2014-561941005d-fp7439r1t-tyc"
PRICED_URL = "https://premier-parts.com.ua/product/fara-liva-perednya-ford-focus-3-usa-2015-2018-f1ez13008gt-fp2819r11p-fps"


def read(name):
    return (FIX / name).read_text(encoding="utf-8")


def test_parse_product_out_of_stock():
    p = parsers.parse_product(read("product.html"), PRODUCT_URL)

    assert p.slug == "fara-liva-perednya-volkswagen-passat-b7-usa-2010-2014-561941005d-fp7439r1t-tyc"
    assert p.name == "Фара ліва передня Volkswagen Passat B7 USA 2010-2014 (561941005D)"
    assert p.sku == "FP7439R1T"
    assert p.manufacturer == "TYC"
    assert (p.make, p.model, p.series) == ("Volkswagen", "Passat B7 USA", "(2011-2014)")
    assert p.condition == "Новий"
    assert p.price == Decimal("0")
    assert p.in_stock is False
    assert p.breadcrumbs == [("Оптика", "optika"), ("Фари передні", "fary-perednie")]
    assert p.image_urls == ["https://premier-parts.com.ua/uploads/product/3556232427_fara-levaya-perednyaya.jpg"]


def test_parse_product_priced_with_gallery():
    p = parsers.parse_product(read("product_priced.html"), PRICED_URL)

    assert p.price == Decimal("3438")
    assert p.in_stock is True
    assert len(p.image_urls) == 3
    assert p.description.startswith("Фара Лів.")
    assert p.make == "Ford"


def test_parse_category_page():
    urls, last_offset = parsers.parse_category_page(read("category.html"))

    assert len(urls) == 12
    assert urls[0].startswith("https://premier-parts.com.ua/product/fara-prava-perednya-toyota-corolla-e150")
    assert last_offset == 3180


def test_parse_home_categories():
    tree = parsers.parse_home_categories(read("home.html"))

    optics = tree[0]
    assert optics.name == "Оптика"
    assert [c.slug for c in optics.children] == [
        "fary-perednie",
        "fonari-zadnie",
        "protivotumannye-fary",
        "ukazateli-povorotov",
    ]
    assert optics.icon_url.endswith(".png")
    assert len(tree) >= 5


def test_parse_home_makes():
    makes = parsers.parse_home_makes(read("home.html"))

    assert (544, "Hyundai") in makes
    assert (574, "Volkswagen") in makes
    assert all(name for _id, name in makes)
    assert len(makes) == len(set(makes))


def test_parse_mark_models():
    links = parsers.parse_mark_models(read("mark.html"), 544)

    accent = [link for link in links if link.model_name == "Accent" and link.years == (2011, 2018)]
    assert accent and accent[0].model_legacy_id == 25775 and accent[0].series_legacy_id == 24560
    assert any(link.model_name == "Elantra AD" for link in links)
    assert all(link.make_legacy_id == 544 for link in links)


@pytest.mark.parametrize(
    "label, years",
    [("(2011-2014)", (2011, 2014)), ("(2018-)", (2018, None)), ("", (None, None)), ("2006 - 2010", (2006, 2010))],
)
def test_parse_years(label, years):
    assert parsers.parse_years(label) == years


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Фара ліва передня Volkswagen Passat", ("left", "front")),
        ("Ліхтар задній правий Mazda 6", ("right", "rear")),
        ("Радіатор охолодження двигуна", ("none", "none")),
        ("Дзеркало праве пасажирське Hyundai", ("right", "none")),
        ("Бампер передній Mercedes W124", ("none", "front")),
    ],
)
def test_parse_side_position(name, expected):
    assert parsers.parse_side_position(name) == expected


def test_parse_page_body():
    title, body = parsers.parse_page_body(read("page.html"))

    assert title == "Доставка та оплата"
    assert "НОВА ПОШТА" in body
    assert "<script" not in body
