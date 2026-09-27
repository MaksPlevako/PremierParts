import hashlib
import secrets
import time
import uuid
from datetime import timedelta
from urllib.parse import urlencode

import httpx
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.utils import timezone
from jwt import PyJWKClient
from rest_framework.decorators import api_view

from .models import CustomerProfile, OAuthFlow, SocialIdentity
from .notifications import notify_new_customer
from .services import normalized_email, rate_limit


def provider_ready(provider: str) -> bool:
    if provider == "google":
        return bool(settings.GOOGLE_OAUTH_CLIENT_ID and settings.GOOGLE_OAUTH_CLIENT_SECRET)
    if provider == "apple":
        return bool(
            settings.SITE_URL.startswith("https://")
            and settings.APPLE_SERVICE_ID and settings.APPLE_TEAM_ID
            and settings.APPLE_KEY_ID and settings.APPLE_PRIVATE_KEY
        )
    return False


def callback_url(provider: str) -> str:
    return f"{settings.SITE_URL}/api/account/oauth/{provider}/callback"


def _failed():
    return HttpResponseRedirect("/account/login?error=oauth")


@api_view(["GET"])
def start(request, provider):
    if not provider_ready(provider):
        return _failed()
    rate_limit("oauth_ip", request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR") or "unknown", 50, 60)
    OAuthFlow.objects.filter(expires_at__lt=timezone.now()).delete()
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    OAuthFlow.objects.create(
        state_hash=hashlib.sha256(state.encode()).hexdigest(), provider=provider,
        nonce=nonce, expires_at=timezone.now() + timedelta(minutes=10),
    )
    redirect_uri = callback_url(provider)
    if provider == "google":
        endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID, "redirect_uri": redirect_uri,
            "response_type": "code", "scope": "openid email profile", "state": state,
            "nonce": nonce, "prompt": "select_account",
        }
    else:
        endpoint = "https://appleid.apple.com/auth/authorize"
        params = {
            "client_id": settings.APPLE_SERVICE_ID, "redirect_uri": redirect_uri,
            "response_type": "code id_token", "response_mode": "form_post",
            "scope": "name email", "state": state, "nonce": nonce,
        }
    response = HttpResponseRedirect(f"{endpoint}?{urlencode(params)}")
    response.set_cookie(
        "pp_oauth_state", state, max_age=600, httponly=True,
        secure=provider == "apple" or settings.SESSION_COOKIE_SECURE,
        samesite="None" if provider == "apple" else "Lax", path="/api/account/oauth/",
    )
    return response


def _verified_claims(provider: str, code: str, nonce: str) -> dict:
    if provider == "google":
        response = httpx.post("https://oauth2.googleapis.com/token", data={
            "code": code, "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "redirect_uri": callback_url(provider), "grant_type": "authorization_code",
        }, timeout=10)
        audience = settings.GOOGLE_OAUTH_CLIENT_ID
        jwks = "https://www.googleapis.com/oauth2/v3/certs"
        issuer = ["https://accounts.google.com", "accounts.google.com"]
    else:
        now = int(time.time())
        client_secret = jwt.encode({
            "iss": settings.APPLE_TEAM_ID, "iat": now, "exp": now + 300,
            "aud": "https://appleid.apple.com", "sub": settings.APPLE_SERVICE_ID,
        }, settings.APPLE_PRIVATE_KEY, algorithm="ES256", headers={"kid": settings.APPLE_KEY_ID})
        response = httpx.post("https://appleid.apple.com/auth/token", data={
            "code": code, "client_id": settings.APPLE_SERVICE_ID,
            "client_secret": client_secret, "redirect_uri": callback_url(provider),
            "grant_type": "authorization_code",
        }, timeout=10)
        audience = settings.APPLE_SERVICE_ID
        jwks = "https://appleid.apple.com/auth/keys"
        issuer = "https://appleid.apple.com"
    response.raise_for_status()
    token = response.json()["id_token"]
    key = PyJWKClient(jwks, cache_jwk_set=True, lifespan=3600, timeout=10).get_signing_key_from_jwt(token).key
    claims = jwt.decode(token, key, algorithms=["RS256"], audience=audience, issuer=issuer, options={"require": ["iss", "aud", "exp", "sub"]})
    if not secrets.compare_digest(str(claims.get("nonce", "")), nonce):
        raise ValueError("OAuth nonce mismatch")
    return claims


@transaction.atomic
def _get_or_link_user(provider: str, claims: dict):
    subject = str(claims["sub"])
    identity = SocialIdentity.objects.select_related("user").filter(provider=provider, subject=subject).first()
    if identity:
        return identity.user if identity.user.is_active else None
    email = normalized_email(str(claims.get("email") or ""))
    if not email or claims.get("email_verified") not in (True, "true", "True"):
        return None
    User = get_user_model()
    user = User.objects.select_for_update().filter(email__iexact=email).first()
    if user and (user.is_staff or user.is_superuser):
        return None
    if user and SocialIdentity.objects.filter(user=user, provider=provider).exists():
        return None
    newly_confirmed = not (user and user.is_active and CustomerProfile.objects.filter(user=user, email_verified=True).exists())
    if not user:
        user = User.objects.create_user(username=f"customer_{uuid.uuid4().hex}", email=email, password=None, is_active=True)
        user.first_name = str(claims.get("given_name") or "")[:150]
        user.save(update_fields=["first_name"])
    elif not user.is_active or not CustomerProfile.objects.filter(user=user, email_verified=True).exists():
        # A pending account has not proved mailbox ownership. Its password must
        # never become usable merely because the real mailbox owner used OAuth.
        user.set_unusable_password()
        user.is_active = True
        user.save(update_fields=["is_active", "password"])
        user.email_challenges.all().delete()
    CustomerProfile.objects.update_or_create(user=user, defaults={"email_key": email, "email_verified": True})
    SocialIdentity.objects.create(user=user, provider=provider, subject=subject)
    if newly_confirmed:
        transaction.on_commit(lambda: notify_new_customer(user, provider), robust=True)
    return user


@api_view(["GET", "POST"])
def callback(request, provider):
    if not provider_ready(provider) or (provider == "google" and request.method != "GET") or (provider == "apple" and request.method != "POST"):
        return _failed()
    state = str(request.data.get("state") if request.method == "POST" else request.query_params.get("state") or "")
    cookie = request.COOKIES.get("pp_oauth_state", "")
    if not state or not cookie or not secrets.compare_digest(state, cookie):
        return _failed()
    state_hash = hashlib.sha256(state.encode()).hexdigest()
    with transaction.atomic():
        flow = OAuthFlow.objects.select_for_update().filter(state_hash=state_hash, provider=provider, expires_at__gt=timezone.now()).first()
        if not flow:
            return _failed()
        nonce = flow.nonce
        flow.delete()
    code = str(request.data.get("code") if request.method == "POST" else request.query_params.get("code") or "")
    if not code:
        return _failed()
    try:
        claims = _verified_claims(provider, code, nonce)
        user = _get_or_link_user(provider, claims)
    except (httpx.HTTPError, jwt.PyJWTError, IntegrityError, KeyError, ValueError, TypeError):
        return _failed()
    if not user:
        return _failed()
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    response = HttpResponseRedirect("/account")
    response.delete_cookie("pp_oauth_state", path="/api/account/oauth/", samesite="None" if provider == "apple" else "Lax")
    return response
