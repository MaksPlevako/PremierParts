"""Keep Forma photos in the configured Django media storage."""

import hashlib
from urllib.parse import urlsplit, urlunsplit

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from apps.catalog.models import ProductImage

from .models import FormaCategory, FormaItem


EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def _category_prefix(link: FormaCategory, client) -> str:
    url = client.category_image_url(link.source_image_path)
    return "categories/forma/" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:20] + "-"


def needs_category_image(link: FormaCategory, client) -> bool:
    if not link.source_image_path:
        return False
    category = link.category
    if category.image and not category.image.name.startswith("categories/forma/"):
        return False
    prefix = _category_prefix(link, client)
    return not (
        category.image and category.image.name.startswith(prefix)
        and default_storage.exists(category.image.name)
    )


def sync_category_image(link: FormaCategory, client, *, downloaded=None) -> bool:
    if not needs_category_image(link, client):
        return False
    url, content, content_type = downloaded if downloaded is not None else client.download_image(
        link.source_image_path, category=True,
    )
    prefix = _category_prefix(link, client)
    path = prefix + hashlib.sha256(content).hexdigest()[:12] + EXTENSIONS[content_type]
    if not default_storage.exists(path):
        default_storage.save(path, ContentFile(content))
    category = link.category
    category.image = path
    category.save(update_fields=["image"])
    return True


def needs_first_image(item: FormaItem, client) -> bool:
    relative = (item.raw_data.get("firstPic") or "").strip()
    if not relative:
        return False
    url = client.image_url(relative)
    return not any(
        image.source_url == url and image.image and default_storage.exists(image.image.name)
        for image in item.product.images.all()
    )


def sync_first_image(item: FormaItem, client, *, downloaded=None) -> bool:
    relative = (item.raw_data.get("firstPic") or "").strip()
    if not relative:
        return False
    expected_url = client.image_url(relative)
    existing = next((img for img in item.product.images.all() if img.source_url == expected_url), None)
    if existing and existing.image and default_storage.exists(existing.image.name):
        return False
    url, content, content_type = downloaded if downloaded is not None else client.download_image(relative)
    parsed = urlsplit(url)
    canonical = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    image = next((img for img in item.product.images.all() if img.source_url.split("?", 1)[0] == canonical), None)
    if image and image.source_url == url and image.image and default_storage.exists(image.image.name):
        return False
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
    content_digest = hashlib.sha256(content).hexdigest()[:12]
    path = f"products/forma/{digest}-{content_digest}{EXTENSIONS[content_type]}"
    if not default_storage.exists(path):
        default_storage.save(path, ContentFile(content))
    if image:
        image.image = path
        image.source_url = url
        image.save(update_fields=["image", "source_url"])
    else:
        ProductImage.objects.create(
            product=item.product, image=path, source_url=url,
            alt=item.product.name, sort=item.product.images.count(),
        )
    return True
