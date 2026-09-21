import pytest

from apps.catalog.services.pricing import live_promotions
from apps.search.documents import load_products, product_document

from .factories import make_generation, make_product, make_promotion

pytestmark = pytest.mark.django_db


def test_product_document_fields():
    gen = make_generation()
    product = make_product(generations=[gen], numbers=["5619 41005-D"], sku="FP7439R1T", price="4000")
    make_promotion(10).products.add(product)

    [loaded] = load_products([product.id])
    doc = product_document(loaded, live_promotions())

    assert doc["id"] == product.id
    assert {"561941005D", "FP7439R1T", "5619 41005-D"} <= set(doc["part_numbers"])
    assert doc["category_ids"] == [product.category_id, product.category.parent_id]
    assert doc["make"] == ["Volkswagen"]
    assert doc["model"] == ["Passat B7 USA"]
    assert doc["family"] == ["Passat"]
    assert doc["generation_ids"] == [gen.id]
    assert doc["price"] == 3600
    assert doc["has_price"] is True
    assert doc["promo"] is True
    assert doc["stock_status"] == "in_stock"
    assert isinstance(doc["created_at"], int)


def test_zero_price_document():
    product = make_product(price="0")
    [loaded] = load_products([product.id])
    doc = product_document(loaded, [])
    assert doc["has_price"] is False and doc["price"] == 0
