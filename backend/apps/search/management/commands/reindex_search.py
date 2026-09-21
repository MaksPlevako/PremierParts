from django.core.management.base import BaseCommand

from apps.search import index


class Command(BaseCommand):
    help = "Rebuild the Meilisearch products index and synonyms from Postgres"

    def handle(self, *args, **opts):
        total = index.reindex_all()
        self.stdout.write(self.style.SUCCESS(f"Проіндексовано товарів: {total}"))
