"""Customer account events that are useful to the support team."""

from django.conf import settings

from apps.orders.notify import notify_manager


def notify_new_customer(user, provider: str) -> None:
    method = {"email": "Email і пароль", "google": "Google", "apple": "Apple"}.get(provider, provider)
    notify_manager(
        f"Новий клієнт: {user.email}",
        [f"Email: {user.email}", f"Ім’я: {user.first_name or '—'}", f"Реєстрація: {method}"],
        context={
            "summary": "Клієнт підтвердив адресу і може користуватися кабінетом.",
            "action_url": f"{settings.SITE_URL}/admin/auth/user/{user.pk}/change/",
            "action_label": "Відкрити клієнта",
        },
    )
