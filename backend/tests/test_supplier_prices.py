from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.catalog.models import StockStatus
from apps.catalog.supplier_prices import (
    SupplierPriceError,
    apply_supplier_price_plan,
    build_supplier_price_plan,
    normalize_sku,
)

from .factories import make_manufacturer, make_product


pytestmark = pytest.mark.django_db


def supplier_file(*rows):
    text = "Brand;ItemNo;Description;Price;КИЕВ1;ItemNo2\r\n"
    text += "".join(f"{brand};{sku};Деталь;{price};>3;{sku}\r\n" for brand, sku, price in rows)
    return text.encode("cp1251")


def test_matches_sku_brand_and_keeps_cyrillic_suffix_distinct():
    normal = make_product(sku="FP5408280", price="150", manufacturer=make_manufacturer("FPS"))
    discount = make_product(sku="FP5408280_УЦН", price="90", manufacturer=make_manufacturer("FPS"))
    other_brand = make_product(sku="FP5408280", price="200", manufacturer=make_manufacturer("TYC"))

    assert normalize_sku("FP 5408 280_УЦН") != normalize_sku("FP 5408 280")
    plan = build_supplier_price_plan(supplier_file(("FPS", "FP 5408 280", "100"), ("FPS", "FP 5408 280_УЦН", "50")))
    assert plan.matched_products == 2
    assert {change.product_id for change in plan.changes} == {normal.id, discount.id}
    assert other_brand.id not in {change.product_id for change in plan.changes}


def test_first_import_establishes_cost_then_reprices_with_existing_margin():
    product = make_product(sku="FP5019902", price="150", stock_status=StockStatus.IN_STOCK, old_price="170")
    first = build_supplier_price_plan(supplier_file(("TYC", "FP 50 19 902", "100")))
    assert first.baseline_products == 1
    assert first.retail_changes == 0
    from django.db import transaction

    with transaction.atomic():
        assert apply_supplier_price_plan(first) == 1
    product.refresh_from_db()
    assert product.price == Decimal("150")
    assert product.supplier_price == Decimal("100")

    second = build_supplier_price_plan(supplier_file(("TYC", "FP 50 19 902", "120")))
    assert second.retail_changes == 1
    with transaction.atomic():
        apply_supplier_price_plan(second)
    product.refresh_from_db()
    assert product.price == Decimal("180")
    assert product.supplier_price == Decimal("120")
    assert product.old_price == Decimal("170")
    assert product.stock_status == StockStatus.IN_STOCK


def test_reports_invalid_conflicting_and_unmatched_rows_without_updating_them():
    product = make_product(sku="FP123", price="80")
    data = supplier_file(
        ("TYC", "FP 123", "40"),
        ("TYC", "FP-123", "45"),
        ("TYC", "FP 999", "20"),
        ("TYC", "FP 888", "27.мар"),
    )
    plan = build_supplier_price_plan(data, "supplier_as_retail")
    assert plan.rows == 4
    assert plan.conflicting_rows == 2
    assert plan.unmatched_rows == 1
    assert plan.invalid_rows == 1
    assert plan.changes == []
    product.refresh_from_db()
    assert product.price == Decimal("80")


def test_known_supplier_brand_alias_and_explicit_wholesale_as_retail():
    product = make_product(sku="XY123", price="50", manufacturer=make_manufacturer("XYG"))
    plan = build_supplier_price_plan(supplier_file(("XINYI", "XY-123", "30,50")), "supplier_as_retail")
    assert plan.matched_products == 1
    assert plan.changes[0].new_price == Decimal("30.50")
    assert plan.changes[0].product_id == product.id


def test_rejects_wrong_format():
    with pytest.raises(SupplierPriceError, match="Brand;ItemNo;Price"):
        build_supplier_price_plan("Артикул;Бренд\nFP123;TYC".encode("cp1251"))


@pytest.fixture
def admin_client(client):
    user = User.objects.create_superuser("price-admin", "price-admin@example.com", "pass12345")
    client.force_login(user)
    return client


def test_admin_preview_then_apply(admin_client, tmp_path, settings):
    settings.IMPORT_CACHE_DIR = tmp_path
    product = make_product(sku="FP123", price="80")
    url = reverse("admin:catalog_product_supplier_price_import")
    response = admin_client.post(
        url,
        {"action": "preview", "mode": "supplier_as_retail", "file": SimpleUploadedFile("price.csv", supplier_file(("TYC", "FP 123", "45")))},
    )
    assert response.status_code == 200
    assert response.context_data["preview"].retail_changes == 1
    product.refresh_from_db()
    assert product.price == Decimal("80")

    token = response.context_data["pending_token"]
    response = admin_client.post(url, {"action": "apply", "token": token})
    assert response.status_code == 302
    product.refresh_from_db()
    assert product.price == Decimal("45")
    assert product.supplier_price == Decimal("45")
    assert not list((tmp_path / "supplier-prices").iterdir())


def test_admin_rechecks_catalog_before_apply(admin_client, tmp_path, settings):
    settings.IMPORT_CACHE_DIR = tmp_path
    product = make_product(sku="FP123", price="80")
    url = reverse("admin:catalog_product_supplier_price_import")
    response = admin_client.post(
        url,
        {"action": "preview", "mode": "supplier_as_retail", "file": SimpleUploadedFile("price.csv", supplier_file(("TYC", "FP 123", "45")))},
    )
    product.price = Decimal("90")
    product.save(update_fields=["price"])
    response = admin_client.post(url, {"action": "apply", "token": response.context_data["pending_token"]})
    assert response.status_code == 200
    assert "Ціни або товари змінилися" in response.content.decode()
    product.refresh_from_db()
    assert product.price == Decimal("90")


def test_supplier_import_requires_admin_change_permission(client):
    user = User.objects.create_user("visitor", "visitor@example.com", "pass12345", is_staff=True)
    client.force_login(user)
    assert client.get(reverse("admin:catalog_product_supplier_price_import")).status_code == 403


def test_supplier_cost_is_not_in_public_product_response(client):
    product = make_product(sku="FP123", supplier_price="40.00")
    response = client.get(f"/api/products/{product.slug}")
    assert response.status_code == 200
    assert "supplier_price" not in response.json()
