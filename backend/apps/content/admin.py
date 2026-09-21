from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import display

from .models import Banner, Page, Promotion, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin, TranslationAdmin):
    fieldsets = (
        (_("Контакти"), {"fields": ("phones", "email", "address", "work_hours", "map_embed_url", "socials")}),
        (_("Оплата та самовивіз"), {"fields": ("iban_details", "pickup_note")}),
        (_("Про компанію та SEO"), {"fields": ("about_short", "seo_title", "seo_description")}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Banner)
class BannerAdmin(ModelAdmin, TranslationAdmin):
    list_display = ("preview", "title", "placement", "theme", "starts_at", "ends_at", "sort", "is_active")
    list_display_links = ("preview", "title")
    list_editable = ("sort", "is_active")
    list_filter = ("placement", "theme", "is_active")
    search_fields = ("title_uk", "subtitle_uk")
    fieldsets = (
        (None, {"fields": ("placement", "theme", "eyebrow", "title", "subtitle", ("link", "cta_label"))}),
        (_("Зображення"), {"fields": ("image", "image_mobile")}),
        (_("Показ"), {"fields": (("starts_at", "ends_at"), ("sort", "is_active"))}),
    )

    @display(description=_("Прев'ю"), image=True)
    def preview(self, obj):
        return obj.image.url if obj.image else None


@admin.register(Promotion)
class PromotionAdmin(ModelAdmin, TranslationAdmin):
    list_display = ("title", "discount_badge", "starts_at", "ends_at", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title_uk",)
    prepopulated_fields = {"slug": ("title_uk",)}
    autocomplete_fields = ("categories", "manufacturers", "products")
    fieldsets = (
        (None, {"fields": ("title", "slug", "discount_percent", "description", "image")}),
        (_("На що діє"), {"fields": ("categories", "manufacturers", "products")}),
        (_("Період"), {"fields": (("starts_at", "ends_at"), ("sort", "is_active"))}),
    )

    @display(description=_("Знижка"), label=True)
    def discount_badge(self, obj):
        return f"−{obj.discount_percent}%"


@admin.register(Page)
class PageAdmin(ModelAdmin, TranslationAdmin):
    list_display = ("title", "slug", "show_in_footer", "sort", "is_active", "open_link")
    list_editable = ("show_in_footer", "sort", "is_active")
    search_fields = ("title_uk", "slug")
    prepopulated_fields = {"slug": ("title_uk",)}
    formfield_overrides = {}

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name.startswith("body"):
            kwargs["widget"] = WysiwygWidget
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    @display(description=_("На сайті"))
    def open_link(self, obj):
        return format_html('<a href="{}" target="_blank">↗</a>', obj.get_absolute_url())
