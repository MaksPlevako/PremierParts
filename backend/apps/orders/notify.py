"""Manager notifications (email + optional Telegram). Failures are logged, never raised."""

import logging

import httpx
from django.conf import settings

from apps.core.email import send_templated_email

log = logging.getLogger(__name__)


def notify_manager(subject: str, lines: list[str], *, template: str = "manager_alert", context: dict | None = None) -> None:
    text = "\n".join([subject, "", *lines])
    try:
        send_templated_email(template, subject, settings.MANAGER_EMAILS, {"lines": lines, **(context or {})})
    except Exception as exc:
        log.warning("email notification failed: %s", exc)
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
        try:
            httpx.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": text},
                timeout=5,
            )
        except Exception as exc:
            log.warning("telegram notification failed: %s", exc)


def _money(value) -> str:
    return f"{value:,.0f}".replace(",", " ") + " ₴" if value else "Ціну уточнюємо"


def order_email_context(order, *, internal: bool) -> dict:
    destination = ", ".join(part for part in (order.city, order.np_branch, order.address) if part)
    action_url = (
        f"{settings.SITE_URL}/admin/orders/order/{order.pk}/change/"
        if internal else f"{settings.SITE_URL}/checkout/success/{order.number}?token={order.access_token}"
    )
    return {
        "order": order,
        "internal": internal,
        "items": [
            {"name": item.name, "sku": item.sku, "qty": item.qty, "total": _money(item.line_total)}
            for item in order.items.all()
        ],
        "total": _money(order.total),
        "delivery": order.get_delivery_method_display(),
        "destination": destination,
        "payment": order.get_payment_method_display(),
        "car": (order.car_snapshot or {}).get("full_label", ""),
        "action_url": action_url,
    }


def notify_order_customer(order) -> None:
    if order.email:
        send_templated_email(
            "order", f"Ваше замовлення {order.number} прийнято", [order.email],
            order_email_context(order, internal=False),
        )


def notify_order_status(order) -> None:
    if order.email:
        send_templated_email(
            "order_status", f"Оновлення замовлення {order.number}", [order.email],
            {
                "order": order,
                "status_label": order.get_status_display(),
                "action_url": f"{settings.SITE_URL}/checkout/success/{order.number}?token={order.access_token}",
            },
        )
