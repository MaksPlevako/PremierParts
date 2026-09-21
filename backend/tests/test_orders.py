import pytest
from rest_framework.test import APIClient

from apps.orders.models import Order

from .factories import make_generation, make_product, make_promotion

pytestmark = pytest.mark.django_db


def payload(product, **kw):
    data = {
        "customer_name": "Олег Петренко",
        "phone": "063 420 39 93",
        "delivery_method": "np_branch",
        "city": "Київ",
        "np_branch": "Відділення №12",
        "payment_method": "iban",
        "items": [{"product_id": product.id, "qty": 2, "price": 1}],  # client price must be ignored
    }
    data.update(kw)
    return data


def test_order_total_is_recalculated_on_server():
    product = make_product(price="3438")
    make_promotion(15).products.add(product)
    gen = make_generation()

    response = APIClient().post("/api/orders", payload(product, car_generation_id=gen.id), format="json")

    assert response.status_code == 201, response.json()
    body = response.json()
    assert body["number"].startswith("PP-")
    order = Order.objects.get(number=body["number"])
    assert order.total == 2922 * 2
    assert order.subtotal == 3438 * 2
    assert order.discount == (3438 - 2922) * 2
    assert order.phone == "+380634203993"
    assert order.car_snapshot["full_label"] == "Volkswagen Passat B7 USA (2011–2014)"
    item = order.items.get()
    assert (item.qty, item.price, item.old_price) == (2, 2922, 3438)


def test_inactive_product_rejected():
    product = make_product(is_active=False)
    response = APIClient().post("/api/orders", payload(product), format="json")
    assert response.status_code == 400
    assert "items" in response.json()


def test_invalid_phone_rejected():
    product = make_product()
    response = APIClient().post("/api/orders", payload(product, phone="123"), format="json")
    assert response.status_code == 400
    assert "phone" in response.json()


def test_np_branch_required_for_nova_poshta():
    product = make_product()
    response = APIClient().post("/api/orders", payload(product, np_branch=""), format="json")
    assert response.status_code == 400
    assert "np_branch" in response.json()


def test_cash_only_for_pickup():
    product = make_product()
    response = APIClient().post("/api/orders", payload(product, payment_method="cash_pickup"), format="json")
    assert response.status_code == 400

    ok = APIClient().post(
        "/api/orders", payload(product, delivery_method="pickup", payment_method="cash_pickup", city=""), format="json"
    )
    assert ok.status_code == 201


def test_quick_order():
    product = make_product(price="0")
    response = APIClient().post("/api/orders/quick", {"phone": "0980701434", "product_id": product.id}, format="json")

    assert response.status_code == 201
    order = Order.objects.get()
    assert order.kind == "quick"
    assert order.total == 0


def test_notification_failure_does_not_break_order(monkeypatch, django_capture_on_commit_callbacks):
    def boom(*args, **kwargs):
        raise RuntimeError("smtp down")

    monkeypatch.setattr("apps.orders.services.notify_manager", boom)
    product = make_product()
    with django_capture_on_commit_callbacks(execute=True):
        response = APIClient().post("/api/orders", payload(product), format="json")
    assert response.status_code == 201


def test_order_detail_requires_token():
    product = make_product()
    body = APIClient().post("/api/orders", payload(product), format="json").json()

    assert APIClient().get(f"/api/orders/{body['number']}").status_code == 404
    detail = APIClient().get(f"/api/orders/{body['number']}", {"token": body["access_token"]}).json()
    assert detail["items"][0]["qty"] == 2
    assert detail["delivery_label"] == "Нова Пошта — відділення"


def test_cart_validate():
    product = make_product(price="1000")
    hidden = make_product(is_active=False)
    body = APIClient().post(
        "/api/cart/validate", {"items": [{"product_id": product.id, "qty": 3}, {"product_id": hidden.id}]}, format="json"
    ).json()

    assert body["total"] == 3000
    availability = {i["product_id"]: i["available"] for i in body["items"]}
    assert availability == {product.id: True, hidden.id: False}


def test_np_disabled_without_key(settings):
    settings.NOVA_POSHTA_API_KEY = ""
    assert APIClient().get("/api/np/cities", {"q": "Київ"}).json() == {"enabled": False, "results": []}
