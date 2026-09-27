import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.forma.models import FormaSyncJob
from apps.forma.sync import run_sync_job


class Command(BaseCommand):
    help = "Synchronize Forma Parts catalog (full or fast)"

    def add_arguments(self, parser):
        parser.add_argument("--mode", choices=["full", "fast"], required=True)
        parser.add_argument("--tree-file", type=Path, help="Confirmed category tree JSON, for an initial staged FULL sync")
        parser.add_argument("--category-id", type=int, action="append", help="Limit item sync to this leaf category; repeatable")

    def handle(self, *args, **options):
        tree = None
        if options["tree_file"]:
            if options["mode"] != "full":
                raise CommandError("--tree-file можна використовувати лише з --mode full")
            try:
                tree = json.loads(options["tree_file"].read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise CommandError(f"Не вдалося прочитати дерево категорій: {exc}") from exc
        job = FormaSyncJob.objects.create(mode=options["mode"])
        try:
            run_sync_job(job, category_tree=tree, category_ids=options["category_id"])
        except Exception as exc:
            raise CommandError(f"Forma sync #{job.pk} failed: {exc}") from exc
        self.stdout.write(
            f"Forma sync #{job.pk}: {job.status}; categories={job.categories_processed}; "
            f"products={job.products_processed}; created={job.products_created}; "
            f"vehicles={job.vehicles_processed}; errors={job.errors_count}"
        )
