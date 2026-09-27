import logging
import os
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone

from apps.forma.models import FormaCategory, FormaSyncJob
from apps.forma.sync import run_sync_job

log = logging.getLogger(__name__)


def schedule_due_jobs():
    if os.environ.get("FORMA_AUTOSYNC", "false").lower() not in {"1", "true", "yes"}:
        return
    if not os.environ.get("FORMA_B2B_TOKEN"):
        return
    if FormaSyncJob.objects.filter(status__in=[FormaSyncJob.Status.PENDING, FormaSyncJob.Status.RUNNING]).exists():
        return
    now = timezone.now()
    full_hours = max(1, int(os.environ.get("FORMA_FULL_INTERVAL_HOURS", "24")))
    fast_hours = max(1, int(os.environ.get("FORMA_FAST_INTERVAL_HOURS", "4")))
    last_full = FormaSyncJob.objects.filter(mode="full").order_by("-created_at").first()
    last_any = FormaSyncJob.objects.order_by("-created_at").first()
    if os.environ.get("FORMA_CATEGORY_TREE_URL") and (
        not last_full or last_full.created_at < now - timedelta(hours=full_hours)
    ):
        FormaSyncJob.objects.create(mode="full")
    elif FormaCategory.objects.filter(is_leaf=True, active=True).exists() and (
        not last_any or last_any.created_at < now - timedelta(hours=fast_hours)
    ):
        FormaSyncJob.objects.create(mode="fast")


def claim_job():
    with transaction.atomic():
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_try_advisory_xact_lock(%s)", [73419027])
                if not cursor.fetchone()[0]:
                    return None
        stale_after = max(1, int(os.environ.get("FORMA_STALE_JOB_HOURS", "6")))
        stale_before = timezone.now() - timedelta(hours=stale_after)
        FormaSyncJob.objects.filter(status=FormaSyncJob.Status.RUNNING).filter(
            Q(heartbeat_at__lt=stale_before) | Q(heartbeat_at__isnull=True, started_at__lt=stale_before)
        ).update(status=FormaSyncJob.Status.FAILED, finished_at=timezone.now())
        if FormaSyncJob.objects.filter(status=FormaSyncJob.Status.RUNNING).exists():
            return None
        job = (
            FormaSyncJob.objects.select_for_update(skip_locked=True)
            .filter(status=FormaSyncJob.Status.PENDING).order_by("created_at").first()
        )
        if job:
            job.status = FormaSyncJob.Status.RUNNING
            job.save(update_fields=["status"])
        return job


class Command(BaseCommand):
    help = "Execute queued Forma sync jobs; optionally schedule periodic full/fast syncs"

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--poll-seconds", type=int, default=15)

    def handle(self, *args, **options):
        while True:
            schedule_due_jobs()
            job = claim_job()
            if job:
                try:
                    run_sync_job(job)
                except Exception:
                    log.exception("forma_sync job=%s failed", job.pk)
            if options["once"]:
                break
            time.sleep(max(1, options["poll_seconds"]))
