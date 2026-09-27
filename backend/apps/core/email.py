"""Shared multipart email delivery for customer and internal notifications."""

from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_templated_email(template: str, subject: str, recipients: list[str], context: dict) -> int:
    recipients = [address for address in recipients if address]
    if not recipients:
        return 0
    site_url = settings.SITE_URL.rstrip("/")
    data = {
        "subject": subject,
        "site_url": site_url,
        "logo_url": "cid:premier-parts-logo",
        "support_email": settings.EMAIL_HOST_USER or "support@premier-parts.com.ua",
        **context,
    }
    message = EmailMultiAlternatives(
        subject=subject,
        body=render_to_string(f"emails/{template}.txt", data).strip() + "\n",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    message.attach_alternative(render_to_string(f"emails/{template}.html", data), "text/html")
    message.mixed_subtype = "related"
    logo = MIMEImage((settings.BASE_DIR / "static/email/logo_white_row.png").read_bytes(), _subtype="png")
    logo.add_header("Content-ID", "<premier-parts-logo>")
    logo.add_header("Content-Disposition", "inline", filename="premier-parts-logo.png")
    message.attach(logo)
    return message.send(fail_silently=False)
