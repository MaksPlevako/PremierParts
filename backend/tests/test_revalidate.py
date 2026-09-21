import httpx
import pytest

from apps.content.models import Banner

from .factories import make_product

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def calls(monkeypatch, settings):
    settings.NEXT_REVALIDATE_URL = "http://frontend:3000/api/revalidate"
    recorded = []

    def fake_post(url, json=None, headers=None, timeout=None):
        recorded.append({"url": url, "tags": json["tags"], "secret": headers["x-revalidate-secret"]})
        return httpx.Response(200)

    monkeypatch.setattr("apps.core.revalidate.httpx.post", fake_post)
    return recorded


def test_saving_product_revalidates_its_tags(calls):
    product = make_product(slug="fara-passat")

    tags = calls[-1]["tags"]
    assert {"product:fara-passat", "products", "home"} <= set(tags)
    assert calls[-1]["secret"] == "dev-revalidate-secret"
    assert product.pk


def test_saving_banner_revalidates_home(calls):
    Banner.objects.create(title="Розпродаж", placement="bento")
    assert "banners" in calls[-1]["tags"] and "home" in calls[-1]["tags"]


def test_network_errors_are_swallowed(monkeypatch, settings):
    settings.NEXT_REVALIDATE_URL = "http://frontend:3000/api/revalidate"

    def boom(*args, **kwargs):
        raise httpx.ConnectError("down")

    monkeypatch.setattr("apps.core.revalidate.httpx.post", boom)
    make_product()  # must not raise


def test_disabled_when_url_empty(monkeypatch, settings):
    settings.NEXT_REVALIDATE_URL = ""
    called = []
    monkeypatch.setattr("apps.core.revalidate.httpx.post", lambda *a, **k: called.append(1))
    make_product()
    assert called == []
