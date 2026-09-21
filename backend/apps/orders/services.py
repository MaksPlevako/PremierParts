"""Order creation: server-side pricing, validation, notification."""

from dataclasses import dataclass, field
from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.catalog.models import Generation, Product
from apps.catalog.services.pricing import effective_price, live_promotions
from apps.catalog.services.queries import car_ref

from .models import Order, OrderItem
from .notify import notify_manager


@dataclass
class OrderInput:
    phone: str
    items: list[dict]  # [{"product_id": int, "qty": int}]
    customer_name: str = ""
    email: str = ""
    delivery_method: str = Order.Delivery.NP_BRANCH
    city: str = ""
    np_branch: str = ""
    address: str = ""
    payment_method: str = Order.Payment.IBAN
    comment: str = ""
    car_generation_id: int | None = None
    kind: str = Order.Kind.REGULAR
    extra_lines: list[str] = field(default_factory=list)


def _money(value: Decimal) -> str:
    return f"{value:,.0f}".replace(",", " ") + " ₴"


@transaction.atomic
def create_order(data: OrderInput) -> Order:
    if not data.items:
        raise ValidationError({"items": ["Кошик порожній"]})
    wanted: dict[int, int] = {}
    for item in data.items:
        qty = int(item.get("qty") or 1)
        if not 1 <= qty <= 99:
            raise ValidationError({"items": ["Кількість має бути від 1 до 99"]})
        wanted[int(item["product_id"])] = wanted.get(int(item["product_id"]), 0) + qty

    products = {
        p.id: p
        for p in Product.objects.select_related("category").filter(id__in=wanted.keys(), is_active=True)
    }
    missing = set(wanted) - set(products)
    if missing:
        raise ValidationError({"items": [f"Товар більше недоступний: {sorted(missing)}"]})

    car = {}
    if data.car_generation_id:
        gen = Generation.objects.select_related("model__make").filter(id=data.car_generation_id).first()
        car = car_ref(gen) if gen else {}

    order = Order.objects.create(
        kind=data.kind,
        customer_name=data.customer_name,
        phone=data.phone,
        email=data.email,
        delivery_method=data.delivery_method,
        city=data.city,
        np_branch=data.np_branch,
        address=data.address,
        payment_method=data.payment_method,
        comment=data.comment,
        car_snapshot=car,
    )
    promos = live_promotions()
    subtotal = total = Decimal("0")
    lines = []
    for product_id, qty in wanted.items():
        product = products[product_id]
        info = effective_price(product, promos)
        unit = info.final
        base = info.old_price if info.sale_price is not None and info.old_price else info.price
        OrderItem.objects.create(
            order=order,
            product=product,
            name=product.name,
            sku=product.sku,
            price=unit,
            old_price=base if base != unit else None,
            qty=qty,
            line_total=unit * qty,
        )
        subtotal += base * qty
        total += unit * qty
        price_label = _money(unit) if unit > 0 else "ціну уточнити"
        lines.append(f"• {product.name} ({product.sku}) × {qty} — {price_label}")
    order.subtotal, order.total, order.discount = subtotal, total, subtotal - total
    order.save(update_fields=["subtotal", "total", "discount"])

    transaction.on_commit(lambda: _notify(order, lines + data.extra_lines))
    return order


def _notify(order: Order, lines: list[str]) -> None:
    try:
        _send_notification(order, lines)
    except Exception:  # an order must never fail because of a notification
        import logging

        logging.getLogger(__name__).exception("order notification failed")


def _send_notification(order: Order, lines: list[str]) -> None:
    head = f"Нове замовлення {order.number}" + (" (в 1 клік)" if order.kind == Order.Kind.QUICK else "")
    notify_manager(
        head,
        [
            f"Клієнт: {order.customer_name or '—'} {order.phone}",
            f"Доставка: {order.get_delivery_method_display()} {order.city} {order.np_branch} {order.address}".strip(),
            f"Оплата: {order.get_payment_method_display()}",
            f"Авто: {order.car_snapshot.get('full_label', '—') if order.car_snapshot else '—'}",
            *lines,
            f"Разом: {_money(order.total)}",
            f"Коментар: {order.comment or '—'}",
        ],
    )


def create_quick_order(phone: str, product_id: int, name: str = "", qty: int = 1, note: str = "", car_generation_id=None) -> Order:
    return create_order(
        OrderInput(
            phone=phone,
            items=[{"product_id": product_id, "qty": qty}],
            customer_name=name,
            comment=note,
            kind=Order.Kind.QUICK,
            car_generation_id=car_generation_id,
            delivery_method=Order.Delivery.NP_BRANCH,
        )
    )
