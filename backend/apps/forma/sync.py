"""Resumable-by-rerun FULL/FAST Forma synchronization."""

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.db import transaction
from django.utils import timezone

from apps.core.revalidate import revalidate_tags, suppress_revalidation
from apps.search import index as search_index

from .client import FormaAuthError, FormaClient, FormaConfigurationError, FormaError
from .images import image_base_configured, needs_first_image, sync_first_image
from .models import FormaCategory, FormaSyncJob
from .normalize import unwrap_list
from .upsert import ProductMatcher, sync_categories, upsert_item, upsert_vehicle_fitment

log = logging.getLogger(__name__)


def _error(job: FormaSyncJob, scope: str, exc: Exception):
    job.errors_count += 1
    message = f"{scope}: {str(exc)[:350]}"
    if len(job.errors) < 100:
        job.errors.append(message)
    log.warning("forma_sync job=%s %s", job.pk, message)


def _fetch_category(client, category):
    return unwrap_list(client.get_items_by_tree_id(category.external_id), "items", "Items", "data", "Data")


def _sync_vehicles(job, client, items):
    with ThreadPoolExecutor(max_workers=client.concurrency) as pool:
        futures = {pool.submit(client.get_item_vehicles, item.item_no): item for item in items}
        for future in as_completed(futures):
            item = futures[future]
            try:
                vehicles = unwrap_list(future.result(), "vehicles", "Vehicles", "data", "Data")
                job.vehicles_processed += len(vehicles)
                for raw in vehicles:
                    try:
                        with transaction.atomic():
                            if upsert_vehicle_fitment(item, raw):
                                job.fitments_created += 1
                    except Exception as exc:
                        _error(job, f"vehicle {item.item_no}", exc)
            except FormaAuthError:
                raise
            except Exception as exc:
                _error(job, f"ItemVehicles {item.item_no}", exc)


def _sync_images(job, client, items):
    pictured = [item for item in items if item.raw_data.get("firstPic")]
    if not pictured:
        return
    if not image_base_configured():
        _error(job, "photos", FormaConfigurationError("FORMA_IMAGE_BASE_URL не налаштовано; фото пропущені"))
        return
    pictured = [item for item in pictured if needs_first_image(item, client)]
    if not pictured:
        return
    with ThreadPoolExecutor(max_workers=client.concurrency) as pool:
        futures = {pool.submit(client.download_image, item.raw_data["firstPic"]): item for item in pictured}
        for future in as_completed(futures):
            item = futures[future]
            try:
                downloaded = future.result()
                sync_first_image(item, client, downloaded=downloaded)
            except FormaAuthError:
                raise
            except Exception as exc:
                _error(job, f"photo {item.item_no}", exc)


def run_sync_job(job: FormaSyncJob, *, client: FormaClient | None = None, category_tree=None, category_ids=None) -> FormaSyncJob:
    """Run one job. Unknown Forma endpoints fail visibly and never use guessed URLs."""
    own_client = client is None
    client = client or FormaClient()
    job.status = FormaSyncJob.Status.RUNNING
    job.started_at = timezone.now()
    job.heartbeat_at = job.started_at
    job.finished_at = None
    job.save(update_fields=["status", "started_at", "heartbeat_at", "finished_at"])
    log.info("forma_sync started job=%s mode=%s", job.pk, job.mode)
    try:
        if job.mode == FormaSyncJob.Mode.FULL:
            tree = category_tree if category_tree is not None else client.get_category_tree()
            with suppress_revalidation(), transaction.atomic():
                categories = sync_categories(tree)
        elif job.mode == FormaSyncJob.Mode.FAST:
            categories = list(FormaCategory.objects.filter(is_leaf=True, active=True).select_related("category"))
        else:
            raise FormaConfigurationError(f"Невідомий режим синхронізації: {job.mode}")
        if category_ids:
            wanted = set(category_ids)
            categories = [category for category in categories if category.external_id in wanted]
        if not categories:
            raise FormaConfigurationError("Немає leaf-категорій Forma для синхронізації")

        matcher = ProductMatcher()
        with suppress_revalidation(), ThreadPoolExecutor(max_workers=client.concurrency) as pool:
            futures = {pool.submit(_fetch_category, client, category): category for category in categories}
            for future in as_completed(futures):
                category = futures[future]
                try:
                    raw_items = future.result()
                except FormaAuthError:
                    raise
                except Exception as exc:
                    _error(job, f"category {category.external_id}", exc)
                    continue
                log.info("forma_sync job=%s category=%s items=%s", job.pk, category.external_id, len(raw_items))
                synced_items = []
                batch_size = max(20, min(int(os.environ.get("FORMA_SYNC_BATCH_SIZE", "200")), 500))
                for start in range(0, len(raw_items), batch_size):
                    with transaction.atomic():
                        for raw in raw_items[start:start + batch_size]:
                            sku = raw.get("itemNo", "") if isinstance(raw, dict) else "?"
                            try:
                                with transaction.atomic():
                                    item, created = upsert_item(raw, category, matcher, fast=job.mode == FormaSyncJob.Mode.FAST)
                                synced_items.append(item)
                                job.products_processed += 1
                                if created:
                                    job.products_created += 1
                                else:
                                    job.products_updated += 1
                            except Exception as exc:
                                _error(job, f"product {sku}", exc)
                    job.heartbeat_at = timezone.now()
                    job.save(update_fields=["heartbeat_at"])
                if job.mode == FormaSyncJob.Mode.FULL:
                    _sync_vehicles(job, client, synced_items)
                    _sync_images(job, client, synced_items)
                product_ids = list(dict.fromkeys(item.product_id for item in synced_items))
                for start in range(0, len(product_ids), 500):
                    try:
                        search_index.upsert_products(product_ids[start:start + 500])
                    except Exception as exc:
                        _error(job, f"search index category {category.external_id}", exc)
                job.categories_processed += 1
                job.heartbeat_at = timezone.now()
                job.save(update_fields=[
                    "categories_processed", "products_processed", "products_created", "products_updated",
                    "vehicles_processed", "fitments_created", "errors_count", "errors", "heartbeat_at",
                ])
        job.status = (
            FormaSyncJob.Status.FAILED if job.errors_count and not job.categories_processed
            else FormaSyncJob.Status.WITH_ERRORS if job.errors_count
            else FormaSyncJob.Status.COMPLETED
        )
        if job.products_processed:
            revalidate_tags(["products", "home", "categories", "makes"])
    except Exception as exc:
        _error(job, "sync", exc)
        job.status = FormaSyncJob.Status.FAILED
        raise
    finally:
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "finished_at", "errors_count", "errors"])
        if own_client:
            client._client.close()
        log.info(
            "forma_sync finished job=%s status=%s categories=%s products=%s vehicles=%s errors=%s",
            job.pk, job.status, job.categories_processed, job.products_processed,
            job.vehicles_processed, job.errors_count,
        )
    return job
