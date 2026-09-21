"""Import catalog data from the legacy premier-parts.com.ua site.

    python manage.py import_premier --limit 3000 --per-category 90
"""

import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.content.models import Page
from apps.core.revalidate import revalidate_tags, suppress_revalidation
from apps.importer import loader, parsers
from apps.importer.fetch import Fetcher

BASE = parsers.BASE
LEGACY_PAGES = ["pro-nas", "dostavka-ta-oplata", "povernennya-ta-obmin", "garantiya", "grafik-roboti", "politics-info"]
MAX_IMAGES_PER_PRODUCT = 4


class Command(BaseCommand):
    help = "Import categories, cars, products (with photos) and pages from premier-parts.com.ua"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=3000, help="Max number of products to import")
        parser.add_argument("--per-category", type=int, default=90, help="Products to take from each leaf category")
        parser.add_argument("--concurrency", type=int, default=4)
        parser.add_argument("--skip-images", action="store_true")
        parser.add_argument("--skip-cars", action="store_true", help="Do not crawl /mark/* pages")
        parser.add_argument("--pages-only", action="store_true")

    def handle(self, *args, **opts):
        started = time.monotonic()
        self.fetcher = Fetcher(settings.IMPORT_CACHE_DIR, concurrency=opts["concurrency"])
        with suppress_revalidation():
            home = self.fetcher.get(BASE + "/")
            self.import_pages()
            if opts["pages_only"]:
                return
            tree = parsers.parse_home_categories(home)
            loader.upsert_category_tree(tree)
            self.stdout.write(f"Категорій: {sum(1 + len(n.children) for n in tree)}")
            if not opts["skip_cars"]:
                self.import_cars(home)
            urls = self.collect_product_urls(tree, opts["per_category"], opts["limit"])
            self.import_products(urls, skip_images=opts["skip_images"])
        revalidate_tags(["products", "home", "categories", "makes", "pages"], immediate=True)
        self.stdout.write(self.style.SUCCESS(f"Готово за {time.monotonic() - started:.0f} с"))

    def import_pages(self):
        for slug in LEGACY_PAGES:
            try:
                title, body = parsers.parse_page_body(self.fetcher.get(f"{BASE}/page/{slug}"))
            except Exception as exc:
                self.stderr.write(f"Сторінка {slug}: {exc}")
                continue
            if title:
                Page.objects.update_or_create(slug=slug, defaults={"title": title, "body": body})
        self.stdout.write(f"Сторінок: {Page.objects.count()}")

    def import_cars(self, home_html: str):
        makes = parsers.parse_home_makes(home_html)

        def fetch(item):
            legacy_id, name = item
            return legacy_id, name, self.fetcher.get(f"{BASE}/mark/{legacy_id}")

        pages = self.fetcher.map(makes, fetch)
        generations = 0
        for legacy_id, name, html in sorted(pages, key=lambda x: x[1]):
            make = loader.upsert_make(legacy_id, name)
            for link in parsers.parse_mark_models(html, legacy_id):
                loader.upsert_generation(make, link)
                generations += 1
        self.stdout.write(f"Марок: {len(makes)}, серій: {generations}")

    def collect_product_urls(self, tree, per_category: int, limit: int) -> list[str]:
        leaves = []
        for node in tree:
            if node.children:
                leaves.extend(child.slug for child in node.children if child.slug)
            elif slug := loader.TOP_CATEGORY_SLUGS.get(node.name):
                leaves.append(slug)
        buckets: dict[str, list[str]] = {}

        def crawl(slug):
            urls: dict[str, None] = {}
            offset, last = 0, None
            while len(urls) < per_category:
                page_url = f"{BASE}/category/{slug}" + (f"/{offset}" if offset else "")
                found, last_offset = parsers.parse_category_page(self.fetcher.get(page_url))
                before = len(urls)
                for url in found:
                    urls.setdefault(url, None)
                last = last_offset if last is None else last
                if len(urls) == before or offset >= (last or 0):
                    break
                offset += 10
            return slug, list(urls)[:per_category]

        for slug, urls in self.fetcher.map(leaves, crawl):
            buckets[slug] = urls
        # round-robin across categories so a limit still gives a balanced demo catalog
        ordered, seen = [], set()
        while len(ordered) < limit and any(buckets.values()):
            for slug in leaves:
                if buckets.get(slug):
                    url = buckets[slug].pop(0)
                    if url not in seen:
                        seen.add(url)
                        ordered.append(url)
        self.stdout.write(f"Посилань на товари: {len(ordered)}")
        return ordered[:limit]

    def import_products(self, urls: list[str], skip_images: bool):
        media_dir = Path(settings.MEDIA_ROOT) / "products" / "legacy"
        errors = []

        def fetch(url):
            parsed = parsers.parse_product(self.fetcher.get(url), url)
            images = []
            if not skip_images:
                for image_url in parsed.image_urls[:MAX_IMAGES_PER_PRODUCT]:
                    path = self.fetcher.download(image_url, media_dir)
                    if path:
                        images.append((image_url, path))
            return parsed, images

        chunk = 100
        done = 0
        for start in range(0, len(urls), chunk):
            batch = urls[start : start + chunk]
            results = self.fetcher.map(batch, fetch, on_error=lambda url, exc: errors.append((url, exc)))
            for parsed, images in results:
                try:
                    loader.upsert_product(parsed, images)
                    done += 1
                except Exception as exc:
                    errors.append((parsed.url, exc))
            self.stdout.write(f"  товарів: {done}/{len(urls)} (помилок: {len(errors)})")
        for url, exc in errors[:20]:
            self.stderr.write(f"  ! {url}: {exc}")
