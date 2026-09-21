from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from apps.core.revalidate import revalidate_tags

from .models import Banner, Page, Promotion, SiteSettings


@receiver([post_save, post_delete], sender=Banner)
def banner_changed(sender, instance, **kwargs):
    revalidate_tags(["banners", "home"])


@receiver([post_save, post_delete], sender=Promotion)
def promotion_changed(sender, instance, **kwargs):
    revalidate_tags(["promotions", f"promotion:{instance.slug}", "products", "home"])


@receiver(m2m_changed, sender=Promotion.products.through)
@receiver(m2m_changed, sender=Promotion.categories.through)
@receiver(m2m_changed, sender=Promotion.manufacturers.through)
def promotion_scope_changed(sender, instance, action, **kwargs):
    if action.startswith("post_"):
        revalidate_tags(["promotions", "products", "home"])


@receiver([post_save, post_delete], sender=Page)
def page_changed(sender, instance, **kwargs):
    revalidate_tags(["pages", f"page:{instance.slug}"])


@receiver(post_save, sender=SiteSettings)
def settings_changed(sender, instance, **kwargs):
    revalidate_tags(["settings", "home"])
