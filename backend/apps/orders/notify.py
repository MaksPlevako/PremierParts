"""Manager notifications (email + optional Telegram). Failures are logged, never raised."""

import logging

import httpx
from django.conf import settings
from django.core.mail import send_mail

log = logging.getLogger(__name__)


def notify_manager(subject: str, lines: list[str]) -> None:
    text = "\n".join([subject, "", *lines])
    try:
        send_mail(subject, text, settings.DEFAULT_FROM_EMAIL, settings.MANAGER_EMAILS, fail_silently=False)
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
