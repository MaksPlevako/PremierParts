import pytest
from django.contrib.auth.models import User

from .factories import make_product

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(client):
    user = User.objects.create_superuser("admin", "admin@example.com", "pass12345")
    client.force_login(user)
    return client


def test_dashboard_renders(admin_client):
    response = admin_client.get("/admin/")
    assert response.status_code == 200
    assert "Замовлення сьогодні" in response.content.decode()


@pytest.mark.parametrize(
    "url",
    [
        "/admin/catalog/product/",
        "/admin/catalog/category/",
        "/admin/catalog/make/",
        "/admin/catalog/generation/",
        "/admin/content/banner/",
        "/admin/content/promotion/",
        "/admin/content/page/",
        "/admin/content/sitesettings/",
        "/admin/orders/order/",
        "/admin/vin/vinrequest/",
        "/admin/search/searchsynonym/",
    ],
)
def test_changelists_render(admin_client, url):
    make_product()
    assert admin_client.get(url).status_code == 200


def test_product_change_form_renders(admin_client):
    product = make_product()
    assert admin_client.get(f"/admin/catalog/product/{product.id}/change/").status_code == 200


def test_dashboard_counts_products_once(admin_client):
    from apps.catalog.models import ProductImage

    product = make_product()
    ProductImage.objects.create(product=product, image="products/a.jpg")
    ProductImage.objects.create(product=product, image="products/b.jpg")
    response = admin_client.get("/admin/")
    assert response.context["kpis"][3]["value"] == "1"
