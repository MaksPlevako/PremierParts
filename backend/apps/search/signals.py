import logging

from django.db import transaction
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from apps.catalog.models import Fitment, PartNumber, Product, ProductImage
from apps.content.models import Promotion
from apps.core.revalidate import is_suppressed

from .models import SearchSynonym

log = logging.getLogger(__name__)


def _later(fn, *args):
    if is_suppressed():
        return

    def run():
        try:
            fn(*args)
        except Exception as exc:  # search is a derived index; never break admin saves
            log.warning("search sync failed: %s", exc)

    transaction.on_commit(run)


@receiver(post_save, sender=Product)
def product_saved(sender, instance, **kwargs):
    from . import index

    _later(index.upsert_products, [instance.id])


@receiver(post_delete, sender=Product)
def product_deleted(sender, instance, **kwargs):
    from . import index

    _later(index.delete_products, [instance.id])


@receiver([post_save, post_delete], sender=Fitment)
@receiver([post_save, post_delete], sender=PartNumber)
@receiver([post_save, post_delete], sender=ProductImage)
def product_part_changed(sender, instance, **kwargs):
    from . import index

    _later(index.upsert_products, [instance.product_id])


@receiver([post_save, post_delete], sender=Promotion)
def promotion_changed(sender, instance, **kwargs):
    from . import index

    _later(index.reindex_all)


@receiver(m2m_changed, sender=Promotion.products.through)
@receiver(m2m_changed, sender=Promotion.categories.through)
@receiver(m2m_changed, sender=Promotion.manufacturers.through)
def promotion_scope_changed(sender, action, **kwargs):
    from . import index

    if action.startswith("post_"):
        _later(index.reindex_all)


@receiver([post_save, post_delete], sender=SearchSynonym)
def synonym_changed(sender, instance, **kwargs):
    from . import index

    _later(index.sync_synonyms)
