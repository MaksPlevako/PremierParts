from functools import wraps
import re

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.conf import settings
from django.db import IntegrityError
from django.http import Http404
from django.middleware.csrf import get_token
from django.middleware.csrf import CsrfViewMiddleware
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.catalog.models import Generation
from apps.catalog.services.pricing import live_promotions
from apps.catalog.services.queries import car_ref, card_queryset, product_cards
from apps.core.normalize import normalize_phone
from apps.orders.models import Order
from apps.orders.serializers import order_summary

from .models import CustomerProfile, EmailChallenge, SavedCar
from .notifications import notify_new_customer
from .oauth import provider_ready
from .services import issue_code, normalized_email, rate_limit as _limited, register_user, validate_new_password, verify_code


class RegisterInput(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, max_length=128, trim_whitespace=False)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)


class EmailCodeInput(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.RegexField(r"^[0-9]{6}$")


class LoginInput(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)


def csrf_required(view):
    """Check CSRF on anonymous auth actions, which DRF SessionAuthentication skips."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        rejection = CsrfViewMiddleware(lambda req: None).process_view(request, lambda req: None, (), {})
        if rejection is not None:
            return rejection
        return view(request, *args, **kwargs)
    return wrapped


def _email_ready():
    if not settings.DEBUG and settings.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend":
        return Response({"detail": "Надсилання email тимчасово недоступне."}, status=503)
    if settings.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend" and not all(
        [settings.EMAIL_HOST, settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD]
    ):
        return Response({"detail": "Надсилання email тимчасово недоступне."}, status=503)
    return None


def _client_ip(request):
    # Nginx overwrites X-Real-IP; production must expose Django only to that proxy.
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR") or "unknown"


def _require_user(request):
    user = request.user
    if not user or not user.is_authenticated or not user.is_active:
        raise Http404
    return user


def _profile_key(user):
    return normalized_email(user.email) or f"staff-{user.pk}@internal.invalid"


def _profile(user):
    profile, _ = CustomerProfile.objects.get_or_create(user=user, defaults={"email_key": _profile_key(user), "email_verified": bool(user.is_staff)})
    return {
        "email": user.email, "first_name": user.first_name, "last_name": user.last_name,
        "email_verified": profile.email_verified, "phone": profile.phone,
        "city": profile.city, "address": profile.address, "np_branch": profile.np_branch,
        "providers": list(user.social_identities.values_list("provider", flat=True)),
    }


@ensure_csrf_cookie
@api_view(["GET"])
def auth_config(request):
    get_token(request)
    return Response({"google": provider_ready("google"), "apple": provider_ready("apple")})


@csrf_required
@api_view(["POST"])
def register(request):
    if (unavailable := _email_ready()) is not None:
        return unavailable
    data = RegisterInput(data=request.data)
    data.is_valid(raise_exception=True)
    email = normalized_email(data.validated_data["email"])
    _limited("register", email, 4, 60)
    _limited("register_ip", _client_ip(request), 20, 60)
    try:
        register_user(email, data.validated_data["password"], data.validated_data.get("first_name", ""))
    except IntegrityError as exc:
        raise ValidationError({"email": "Обліковий запис із цією адресою вже існує."}) from exc
    return Response({"detail": "Код підтвердження надіслано на email."}, status=status.HTTP_201_CREATED)


@csrf_required
@api_view(["POST"])
def verify_email(request):
    data = EmailCodeInput(data=request.data)
    data.is_valid(raise_exception=True)
    email = normalized_email(data.validated_data["email"])
    _limited("verify", email, 10, 10)
    user = verify_code(email, data.validated_data["code"], EmailChallenge.Purpose.VERIFY)
    user.is_active = True
    user.save(update_fields=["is_active"])
    CustomerProfile.objects.update_or_create(user=user, defaults={"email_key": normalized_email(user.email), "email_verified": True})
    notify_new_customer(user, "email")
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return Response(_profile(user))


@csrf_required
@api_view(["POST"])
def resend_email(request):
    if (unavailable := _email_ready()) is not None:
        return unavailable
    email_field = serializers.EmailField()
    email = normalized_email(email_field.run_validation(request.data.get("email")))
    _limited("resend", email, 5, 60)
    _limited("resend_ip", _client_ip(request), 30, 60)
    user = get_user_model().objects.filter(email__iexact=email, is_active=False, is_staff=False).first()
    if user:
        issue_code(user, EmailChallenge.Purpose.VERIFY)
    return Response({"detail": "Якщо адреса очікує підтвердження, код надіслано."})


@csrf_required
@api_view(["POST"])
def sign_in(request):
    data = LoginInput(data=request.data)
    data.is_valid(raise_exception=True)
    email = normalized_email(data.validated_data["email"])
    _limited("login", email, 10, 10)
    _limited("login_ip", _client_ip(request), 100, 10)
    user = get_user_model().objects.filter(email__iexact=email).first()
    authenticated = authenticate(request, username=user.username, password=data.validated_data["password"]) if user else None
    if not authenticated:
        if user and not user.is_active and user.check_password(data.validated_data["password"]):
            return Response({"detail": "Підтвердіть email кодом із листа.", "email_verification_required": True}, status=403)
        return Response({"detail": "Невірний email або пароль."}, status=400)
    if not _profile(authenticated)["email_verified"] and not authenticated.is_staff:
        return Response({"detail": "Підтвердіть email.", "email_verification_required": True}, status=403)
    login(request, authenticated)
    return Response(_profile(authenticated))


@csrf_required
@api_view(["POST"])
def sign_out(request):
    logout(request)
    return Response({"ok": True})


@csrf_required
@api_view(["POST"])
def request_reset(request):
    if (unavailable := _email_ready()) is not None:
        return unavailable
    email = normalized_email(serializers.EmailField().run_validation(request.data.get("email")))
    _limited("reset", email, 5, 60)
    _limited("reset_ip", _client_ip(request), 30, 60)
    user = get_user_model().objects.filter(email__iexact=email, is_active=True, is_staff=False).first()
    if user:
        issue_code(user, EmailChallenge.Purpose.RESET)
    return Response({"detail": "Якщо обліковий запис існує, код надіслано."})


@csrf_required
@api_view(["POST"])
def confirm_reset(request):
    data = EmailCodeInput(data=request.data)
    data.is_valid(raise_exception=True)
    password = serializers.CharField(min_length=8, max_length=128, trim_whitespace=False).run_validation(request.data.get("password"))
    validate_new_password(password)
    email = normalized_email(data.validated_data["email"])
    _limited("confirm_reset", email, 10, 10)
    user = verify_code(email, data.validated_data["code"], EmailChallenge.Purpose.RESET)
    user.set_password(password)
    user.save(update_fields=["password"])
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return Response(_profile(user))


@api_view(["GET", "PATCH"])
def profile(request):
    user = _require_user(request)
    if request.method == "GET":
        return Response(_profile(user))
    allowed = {"first_name": 150, "last_name": 150, "phone": 20, "city": 160, "address": 255, "np_branch": 255}
    unknown = set(request.data) - set(allowed)
    if unknown:
        raise ValidationError({"detail": "Невідомі поля профілю."})
    profile_obj, _ = CustomerProfile.objects.get_or_create(user=user, defaults={"email_key": _profile_key(user)})
    for key, max_length in allowed.items():
        if key not in request.data:
            continue
        value = serializers.CharField(max_length=max_length, allow_blank=True).run_validation(request.data[key])
        if key == "phone" and value:
            value = normalize_phone(value)
            if not value:
                raise ValidationError({"phone": "Вкажіть номер у форматі +380XXXXXXXXX"})
        setattr(user if key in ("first_name", "last_name") else profile_obj, key, value.strip())
    user.save(update_fields=["first_name", "last_name"])
    profile_obj.save()
    return Response(_profile(user))


def _car_data(car):
    return {"id": car.id, "nickname": car.nickname, "vin": car.vin, "car": car_ref(car.generation)}


@api_view(["GET", "POST"])
def garage(request):
    user = _require_user(request)
    if request.method == "GET":
        return Response([_car_data(c) for c in SavedCar.objects.filter(user=user).select_related("generation__model__make")])
    generation_id = serializers.IntegerField(min_value=1).run_validation(request.data.get("generation_id"))
    generation = Generation.objects.select_related("model__make").filter(pk=generation_id).first()
    if not generation:
        raise ValidationError({"generation_id": "Автомобіль не знайдено."})
    nickname = serializers.CharField(max_length=80, allow_blank=True, required=False).run_validation(request.data.get("nickname", ""))
    vin = str(request.data.get("vin") or "").strip().upper()
    if vin and not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", vin):
        raise ValidationError({"vin": "VIN має містити 17 символів без I, O та Q."})
    car = SavedCar.objects.create(user=user, generation=generation, nickname=nickname.strip(), vin=vin)
    return Response(_car_data(car), status=201)


@api_view(["DELETE"])
def garage_item(request, pk):
    user = _require_user(request)
    deleted, _ = SavedCar.objects.filter(pk=pk, user=user).delete()
    if not deleted:
        raise Http404
    return Response(status=204)


@api_view(["GET"])
def my_orders(request):
    user = _require_user(request)
    orders = Order.objects.filter(user=user).prefetch_related("items__product")[:50]
    return Response([order_summary(o) for o in orders])


@api_view(["GET"])
def my_order(request, number):
    user = _require_user(request)
    order = Order.objects.filter(number=number, user=user).prefetch_related("items__product").first()
    if not order:
        raise Http404
    return Response(order_summary(order))


@api_view(["GET"])
def recommendations(request):
    user = _require_user(request)
    generation_ids = list(SavedCar.objects.filter(user=user).values_list("generation_id", flat=True))
    bought = list(Order.objects.filter(user=user).values_list("items__product__category_id", flat=True).distinct())
    bought = [category for category in bought if category]
    if not generation_ids:
        return Response({"reason": "add_car", "products": []})
    queryset = card_queryset().filter(fitments__generation_id__in=generation_ids)
    if bought:
        queryset = queryset.filter(category_id__in=bought)
    preferred = queryset.filter(category_id__in=bought) if bought else queryset
    selected = list(preferred.distinct().order_by("-popularity", "name")[:12])
    if not selected and bought:
        selected = list(queryset.distinct().order_by("-popularity", "name")[:12])
    products = product_cards(selected, live_promotions())
    return Response({"reason": "garage_and_purchases" if bought else "garage", "products": products})
