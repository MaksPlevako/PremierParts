import re

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from rest_framework.test import APIClient

from apps.accounts.models import CustomerProfile, EmailChallenge, SavedCar, SocialIdentity
from apps.accounts.oauth import _get_or_link_user
from apps.orders.models import Order
from .factories import make_generation, make_product


pytestmark = pytest.mark.django_db


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_registration_code_and_session():
    client = APIClient()
    result = client.post("/api/account/register", {"email": "USER@example.com", "password": "safe-password-123", "first_name": "Олена"}, format="json")
    assert result.status_code == 201
    user = get_user_model().objects.get(email="user@example.com")
    assert not user.is_active
    assert len(mail.outbox) == 1
    assert mail.outbox[0].alternatives[0][1] == "text/html"
    assert "Premier Parts" in mail.outbox[0].alternatives[0][0]
    assert "cid:premier-parts-logo" in mail.outbox[0].alternatives[0][0]
    assert "Content-ID: <premier-parts-logo>" in mail.outbox[0].message().as_string()
    assert client.post("/api/account/login", {"email": user.email, "password": "safe-password-123"}, format="json").status_code == 403
    code = re.search(r"Ваш код: (\d{6})", mail.outbox[-1].body).group(1)
    assert client.post("/api/account/verify-email", {"email": user.email, "code": "000000" if code != "000000" else "111111"}, format="json").status_code == 400
    assert EmailChallenge.objects.get(user=user).attempts == 1
    result = client.post("/api/account/verify-email", {"email": user.email, "code": code}, format="json")
    assert result.status_code == 200
    assert result.json()["email_verified"] is True
    assert client.get("/api/account/profile").status_code == 200
    assert not EmailChallenge.objects.filter(user=user).exists()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", MANAGER_EMAILS=["support@premier-parts.com.ua"])
def test_verified_customer_notifies_support(mailoutbox):
    client = APIClient()
    client.post("/api/account/register", {"email": "new@example.com", "password": "safe-password-123"}, format="json")
    assert len(mailoutbox) == 1  # No alert for an unverified signup.
    code = re.search(r"Ваш код: (\d{6})", mailoutbox[0].body).group(1)
    assert client.post("/api/account/verify-email", {"email": "new@example.com", "code": code}, format="json").status_code == 200
    assert len(mailoutbox) == 2
    assert mailoutbox[1].to == ["support@premier-parts.com.ua"]
    assert "new@example.com" in mailoutbox[1].body
    assert "<html" in mailoutbox[1].alternatives[0][0]


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", MANAGER_EMAILS=["support@premier-parts.com.ua"])
def test_new_oauth_customer_notifies_support(mailoutbox, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        user = _get_or_link_user("google", {"sub": "new-google-user", "email": "oauth@example.com", "email_verified": True})
    assert user.email == "oauth@example.com"
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["support@premier-parts.com.ua"]
    assert "Google" in mailoutbox[0].body


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", MANAGER_EMAILS=["support@premier-parts.com.ua"])
def test_oauth_activation_of_pending_signup_notifies_support(mailoutbox, django_capture_on_commit_callbacks):
    user = get_user_model().objects.create_user(username="pending-google", email="pending@example.com", password="old-password", is_active=False)
    CustomerProfile.objects.create(user=user, email_key=user.email)
    with django_capture_on_commit_callbacks(execute=True):
        _get_or_link_user("google", {"sub": "g-pending", "email": user.email, "email_verified": True})
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["support@premier-parts.com.ua"]
    assert "pending@example.com" in mailoutbox[0].body


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
    EMAIL_HOST="mx1.mirohost.net",
    EMAIL_HOST_USER="support@premier-parts.com.ua",
    EMAIL_HOST_PASSWORD="",
)
def test_registration_requires_smtp_credentials():
    result = APIClient().post(
        "/api/account/register",
        {"email": "pending@example.com", "password": "safe-password-123"},
        format="json",
    )
    assert result.status_code == 503
    assert not get_user_model().objects.filter(email="pending@example.com").exists()


def test_oauth_links_verified_email_without_duplicate():
    User = get_user_model()
    user = User.objects.create_user(username="member", email="person@example.com", password="abc123456", is_active=True)
    CustomerProfile.objects.create(user=user, email_key=user.email, email_verified=True)
    linked = _get_or_link_user("google", {"sub": "google-123", "email": "PERSON@example.com", "email_verified": True})
    assert linked.pk == user.pk
    assert SocialIdentity.objects.get(provider="google", subject="google-123").user_id == user.pk
    assert User.objects.filter(email__iexact=user.email).count() == 1
    assert _get_or_link_user("google", {"sub": "google-123", "email": "", "email_verified": False}).pk == user.pk


def test_oauth_does_not_activate_unverified_password():
    User = get_user_model()
    user = User.objects.create_user(username="pending", email="target@example.com", password="known-to-attacker", is_active=False)
    CustomerProfile.objects.create(user=user, email_key=user.email)
    linked = _get_or_link_user("google", {"sub": "g-456", "email": user.email, "email_verified": True})
    user.refresh_from_db()
    assert linked.pk == user.pk
    assert user.is_active
    assert not user.has_usable_password()
    assert _get_or_link_user("apple", {"sub": "a-1", "email": "unverified@example.com", "email_verified": False}) is None


def test_garage_and_orders_are_private():
    User = get_user_model()
    owner = User.objects.create_user(username="owner", email="owner@example.com", password="abc123456")
    other = User.objects.create_user(username="other", email="other@example.com", password="abc123456")
    CustomerProfile.objects.create(user=owner, email_key=owner.email, email_verified=True)
    CustomerProfile.objects.create(user=other, email_key=other.email, email_verified=True)
    gen = make_generation()
    car = SavedCar.objects.create(user=owner, generation=gen)
    order = Order.objects.create(user=owner, phone="+380634203993", email=owner.email)
    client = APIClient()
    client.force_login(other)
    assert client.get("/api/account/garage").json() == []
    assert client.delete(f"/api/account/garage/{car.pk}").status_code == 404
    assert client.get("/api/account/orders").json() == []
    assert client.get(f"/api/account/orders/{order.number}").status_code == 404
    client.force_login(owner)
    assert len(client.get("/api/account/garage").json()) == 1
    assert client.get(f"/api/account/orders/{order.number}").status_code == 200


def test_signed_in_checkout_appears_in_history():
    user = get_user_model().objects.create_user(username="buyer", email="buyer@example.com", password="abc123456")
    CustomerProfile.objects.create(user=user, email_key=user.email, email_verified=True)
    product = make_product()
    client = APIClient()
    client.force_login(user)
    created = client.post("/api/orders", {
        "customer_name": "Покупець", "phone": "063 420 39 93", "email": user.email,
        "delivery_method": "pickup", "payment_method": "iban",
        "items": [{"product_id": product.id, "qty": 1}],
    }, format="json")
    assert created.status_code == 201
    assert Order.objects.get(number=created.json()["number"]).user_id == user.pk
    assert len(client.get("/api/account/orders").json()) == 1


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_csrf_required_for_registration():
    client = APIClient(enforce_csrf_checks=True)
    assert client.post("/api/account/register", {"email": "a@example.com", "password": "abc123456"}, format="json").status_code == 403
    assert client.get("/api/account/config").status_code == 200
    token = client.cookies["csrftoken"].value
    result = client.post("/api/account/register", {"email": "a@example.com", "password": "abc123456"}, format="json", HTTP_X_CSRFTOKEN=token)
    assert result.status_code == 201
