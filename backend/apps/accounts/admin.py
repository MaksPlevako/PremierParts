from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import CustomerProfile, SavedCar, SocialIdentity


@admin.register(CustomerProfile)
class CustomerProfileAdmin(ModelAdmin):
    list_display = ("user", "email_key", "email_verified", "phone", "updated_at")
    search_fields = ("email_key", "phone", "user__first_name", "user__last_name")
    readonly_fields = ("user", "email_key", "email_verified", "updated_at")

    def has_add_permission(self, request):
        return False


@admin.register(SavedCar)
class SavedCarAdmin(ModelAdmin):
    list_display = ("user", "generation", "nickname", "vin", "created_at")
    search_fields = ("user__email", "nickname", "vin")


@admin.register(SocialIdentity)
class SocialIdentityAdmin(ModelAdmin):
    list_display = ("user", "provider", "created_at")
    search_fields = ("user__email", "provider")
    readonly_fields = ("user", "provider", "subject", "created_at")

    def has_add_permission(self, request):
        return False
