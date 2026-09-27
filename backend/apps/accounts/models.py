from django.conf import settings
from django.db import models
from django.utils import timezone


class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile")
    email_key = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=160, blank=True)
    address = models.CharField(max_length=255, blank=True)
    np_branch = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class EmailChallenge(models.Model):
    class Purpose(models.TextChoices):
        VERIFY = "verify", "Verify email"
        RESET = "reset", "Reset password"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_challenges")
    purpose = models.CharField(max_length=8, choices=Purpose.choices)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    sent_at = models.DateTimeField(default=timezone.now)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "purpose"], name="unique_email_challenge")]


class SocialIdentity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="social_identities")
    provider = models.CharField(max_length=12)
    subject = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "subject"], name="unique_social_subject"),
            models.UniqueConstraint(fields=["user", "provider"], name="unique_user_social_provider"),
        ]


class OAuthFlow(models.Model):
    state_hash = models.CharField(max_length=64, unique=True)
    provider = models.CharField(max_length=12)
    nonce = models.CharField(max_length=64)
    expires_at = models.DateTimeField(db_index=True)


class AuthRateLimit(models.Model):
    key_hash = models.CharField(max_length=64, unique=True)
    count = models.PositiveSmallIntegerField(default=0)
    window_start = models.DateTimeField(default=timezone.now)


class SavedCar(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_cars")
    generation = models.ForeignKey("catalog.Generation", on_delete=models.CASCADE)
    nickname = models.CharField(max_length=80, blank=True)
    vin = models.CharField(max_length=17, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
