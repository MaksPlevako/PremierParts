from modeltranslation.translator import TranslationOptions, register

from .models import Banner, Page, Promotion, SiteSettings


@register(SiteSettings)
class SiteSettingsTranslation(TranslationOptions):
    fields = ("address", "work_hours", "iban_details", "pickup_note", "about_short", "seo_title", "seo_description")


@register(Banner)
class BannerTranslation(TranslationOptions):
    fields = ("title", "subtitle", "eyebrow", "cta_label")


@register(Promotion)
class PromotionTranslation(TranslationOptions):
    fields = ("title", "description")


@register(Page)
class PageTranslation(TranslationOptions):
    fields = ("title", "body", "seo_title", "seo_description")
