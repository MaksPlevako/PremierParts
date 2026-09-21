"""Meilisearch index: settings, (re)indexing, synonyms and raw search."""

import logging
from functools import lru_cache

import meilisearch
from django.conf import settings

from apps.catalog.models import CarModel, Make
from apps.catalog.services.pricing import live_promotions

from .documents import load_products, product_document

log = logging.getLogger(__name__)

INDEX_SETTINGS = {
    "searchableAttributes": [
        "name",
        "part_numbers",
        "sku",
        "make",
        "model",
        "family",
        "generation",
        "category",
        "manufacturer",
    ],
    "filterableAttributes": [
        "category_ids",
        "manufacturer_id",
        "make_ids",
        "model_ids",
        "generation_ids",
        "side",
        "position",
        "stock_status",
        "price",
        "has_price",
        "promo",
        "promotion_ids",
    ],
    "sortableAttributes": ["price", "popularity", "created_at"],
    "rankingRules": ["words", "typo", "proximity", "attribute", "sort", "exactness", "popularity:desc"],
    "typoTolerance": {
        "enabled": True,
        "minWordSizeForTypos": {"oneTypo": 4, "twoTypos": 8},
        "disableOnAttributes": ["part_numbers", "sku"],
    },
    "pagination": {"maxTotalHits": 5000},
    "faceting": {"maxValuesPerFacet": 200},
}


@lru_cache(maxsize=1)
def client() -> meilisearch.Client:
    return meilisearch.Client(settings.MEILI_URL, settings.MEILI_MASTER_KEY, timeout=5)


def index():
    return client().index(settings.MEILI_INDEX)


def _wait(task) -> None:
    client().wait_for_task(task.task_uid, timeout_in_ms=120_000, interval_in_ms=100)


def ensure_settings() -> None:
    try:
        client().get_index(settings.MEILI_INDEX)
    except meilisearch.errors.MeilisearchApiError:
        _wait(client().create_index(settings.MEILI_INDEX, {"primaryKey": "id"}))
    _wait(index().update_settings(INDEX_SETTINGS))


def reindex_all(batch: int = 1000) -> int:
    ensure_settings()
    promos = live_promotions()
    _wait(index().delete_all_documents())
    total = 0
    docs: list[dict] = []
    for product in load_products().iterator(chunk_size=500):
        docs.append(product_document(product, promos))
        if len(docs) >= batch:
            _wait(index().add_documents(docs, primary_key="id"))
            total += len(docs)
            docs = []
    if docs:
        _wait(index().add_documents(docs, primary_key="id"))
        total += len(docs)
    sync_synonyms()
    return total


def upsert_products(ids: list[int]) -> None:
    ids = list(set(ids))
    if not ids:
        return
    promos = live_promotions()
    products = list(load_products(ids))
    docs = [product_document(p, promos) for p in products]
    if docs:
        index().add_documents(docs, primary_key="id")
    missing = set(ids) - {p.id for p in products}
    if missing:
        index().delete_documents(list(missing))


def delete_products(ids: list[int]) -> None:
    if ids:
        index().delete_documents(list(ids))


def build_synonyms() -> dict[str, list[str]]:
    from .car_aliases import translit_variants
    from .models import SearchSynonym

    groups: list[set[str]] = []
    for syn in SearchSynonym.objects.filter(is_active=True):
        groups.append({syn.term.lower(), *syn.synonym_list()})
    names = set(Make.objects.values_list("name", flat=True)) | set(CarModel.objects.values_list("family", flat=True))
    for name in names:
        word = (name or "").lower()
        if word and word.isascii() and " " not in word and len(word) >= 3:
            variants = translit_variants(word)
            if variants:
                groups.append({word, *variants})
    synonyms: dict[str, set[str]] = {}
    for group in groups:
        for word in group:
            synonyms.setdefault(word, set()).update(group - {word})
    return {k: sorted(v) for k, v in synonyms.items() if v}


def sync_synonyms() -> None:
    _wait(index().update_synonyms(build_synonyms()))


def search(q: str, *, filters=None, facets=None, sort=None, page: int = 1, hits_per_page: int = 24, **extra) -> dict:
    params = {
        "filter": filters or [],
        "facets": facets or [],
        "page": page,
        "hitsPerPage": hits_per_page,
        "attributesToRetrieve": ["id"],
        **extra,
    }
    if sort:
        params["sort"] = sort
    return index().search(q or "", params)
