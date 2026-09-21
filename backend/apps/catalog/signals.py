from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.core.revalidate import revalidate_tags

from .models import CarModel, Category, Fitment, Generation, Make, Manufacturer, PartNumber, Product, ProductImage


@receiver([post_save, post_delete], sender=Product)
def product_changed(sender, instance, **kwargs):
    revalidate_tags([f"product:{instance.slug}", "products", "home"])


@receiver([post_save, post_delete], sender=ProductImage)
@receiver([post_save, post_delete], sender=PartNumber)
@receiver([post_save, post_delete], sender=Fitment)
def product_part_changed(sender, instance, **kwargs):
    slug = Product.objects.filter(pk=instance.product_id).values_list("slug", flat=True).first()
    revalidate_tags([f"product:{slug}", "products"] if slug else ["products"])


@receiver([post_save, post_delete], sender=Category)
def category_changed(sender, instance, **kwargs):
    revalidate_tags(["categories", f"category:{instance.slug}", "home"])


@receiver([post_save, post_delete], sender=Make)
@receiver([post_save, post_delete], sender=CarModel)
@receiver([post_save, post_delete], sender=Generation)
@receiver([post_save, post_delete], sender=Manufacturer)
def cars_changed(sender, instance, **kwargs):
    revalidate_tags(["makes", "products", "home"])
