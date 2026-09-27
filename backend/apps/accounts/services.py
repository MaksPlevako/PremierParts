import secrets
import uuid
import hashlib
import hmac
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.core.email import send_templated_email
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from rest_framework.exceptions import ValidationError

from .models import AuthRateLimit, CustomerProfile, EmailChallenge


def normalized_email(value: str) -> str:
    return value.strip().lower()


def rate_limit(action: str, key: str, limit: int = 5, minutes: int = 10):
    digest = hmac.new(settings.SECRET_KEY.encode(), f"{action}:{key.lower()}".encode(), hashlib.sha256).hexdigest()
    now = timezone.now()
    with transaction.atomic():
        row, _ = AuthRateLimit.objects.select_for_update().get_or_create(key_hash=digest)
        if row.window_start <= now - timedelta(minutes=minutes):
            row.window_start, row.count = now, 0
        row.count += 1
        row.save(update_fields=["window_start", "count"])
        if row.count > limit:
            raise ValidationError({"detail": "Забагато спроб. Спробуйте пізніше."})


def validate_new_password(password: str, user=None) -> None:
    try:
        validate_password(password, user)
    except DjangoValidationError as exc:
        raise ValidationError({"password": exc.messages}) from exc


@transaction.atomic
def issue_code(user, purpose: str, *, cooldown: bool = True) -> None:
    now = timezone.now()
    old = EmailChallenge.objects.filter(user=user, purpose=purpose).first()
    if cooldown and old and old.sent_at > now - timedelta(seconds=60):
        raise ValidationError({"detail": "Повторно надіслати код можна через 60 секунд."})
    code = f"{secrets.randbelow(1_000_000):06d}"
    EmailChallenge.objects.update_or_create(
        user=user,
        purpose=purpose,
        defaults={
            "code_hash": make_password(code),
            "expires_at": now + timedelta(minutes=10),
            "sent_at": now,
            "attempts": 0,
        },
    )
    verifying = purpose == EmailChallenge.Purpose.VERIFY
    subject = "Код підтвердження Premier Parts" if verifying else "Відновлення пароля Premier Parts"
    send_templated_email("code", subject, [user.email], {
        "code": code,
        "heading": "Підтвердіть email" if verifying else "Відновіть пароль",
        "introduction": "Введіть цей код на сайті, щоб завершити реєстрацію." if verifying else "Введіть цей код на сайті, щоб встановити новий пароль.",
    })


@transaction.atomic
def register_user(email: str, password: str, first_name: str = ""):
    User = get_user_model()
    email = normalized_email(email)
    if User.objects.filter(email__iexact=email).exists():
        raise ValidationError({"email": "Обліковий запис із цією адресою вже існує."})
    validate_new_password(password)
    user = User.objects.create_user(username=f"customer_{uuid.uuid4().hex}", email=email, password=password, first_name=first_name.strip()[:150], is_active=False)
    CustomerProfile.objects.create(user=user, email_key=email)
    issue_code(user, EmailChallenge.Purpose.VERIFY, cooldown=False)
    return user


def verify_code(email: str, code: str, purpose: str):
    User = get_user_model()
    with transaction.atomic():
        user = User.objects.select_for_update().filter(email__iexact=normalized_email(email), is_staff=False).first()
        challenge = EmailChallenge.objects.select_for_update().filter(user=user, purpose=purpose).first() if user else None
        if not challenge or challenge.expires_at <= timezone.now() or challenge.attempts >= 5:
            error = "Код недійсний або термін його дії минув."
        else:
            valid = len(code) == 6 and code.isascii() and code.isdigit() and check_password(code, challenge.code_hash)
            challenge.attempts += 1
            challenge.save(update_fields=["attempts"])
            if valid:
                challenge.delete()
                error = None
            else:
                error = "Невірний код."
    if error:
        raise ValidationError({"code": error})
    return user
