"""The only HTTP boundary for the authenticated Forma B2B API."""

import json
import logging
import os
import threading
import time
from urllib.parse import urljoin, urlparse

import httpx

log = logging.getLogger(__name__)
DEFAULT_IMAGE_BASE_URL = "https://img2.ad.ua/imgs/"
DEFAULT_CATEGORY_IMAGE_BASE_URL = "https://img2.ad.ua/imgs/group-pic/"


class FormaError(RuntimeError):
    pass


class FormaConfigurationError(FormaError):
    pass


class FormaAuthError(FormaError):
    pass


class FormaAPIError(FormaError):
    pass


class FormaClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        token: str | None = None,
        category_tree_url: str | None = None,
        category_tree_method: str | None = None,
        category_tree_body: str | None = None,
        concurrency: int | None = None,
        delay: float | None = None,
        transport: httpx.BaseTransport | None = None,
    ):
        self.base_url = (base_url or os.environ.get("FORMA_API_BASE_URL") or "https://ecom.ad.ua").rstrip("/")
        self.token = token if token is not None else os.environ.get("FORMA_B2B_TOKEN", "")
        self.category_tree_url = category_tree_url or os.environ.get("FORMA_CATEGORY_TREE_URL") or self.base_url + "/api/content/Catalog"
        self.category_tree_method = (category_tree_method or os.environ.get("FORMA_CATEGORY_TREE_METHOD") or "POST").upper()
        self.category_tree_body = category_tree_body if category_tree_body is not None else os.environ.get("FORMA_CATEGORY_TREE_BODY", "")
        self.concurrency = max(1, min(int(concurrency or os.environ.get("FORMA_SYNC_CONCURRENCY", "5")), 20))
        self.delay = max(0.0, float(delay if delay is not None else os.environ.get("FORMA_SYNC_DELAY", "0.2")))
        self._client = httpx.Client(timeout=httpx.Timeout(30, connect=10), transport=transport)
        self._lock = threading.Lock()
        self._slots = threading.BoundedSemaphore(self.concurrency)
        self._last_request = 0.0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._client.close()

    def _throttle(self):
        with self._lock:
            wait = self._last_request + self.delay - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last_request = time.monotonic()

    def _request(self, method: str, url: str, *, json_body=None):
        if not self.token:
            raise FormaConfigurationError("FORMA_B2B_TOKEN не налаштовано")
        parsed_url = urlparse(url)
        parsed_base = urlparse(self.base_url)
        if parsed_url.scheme != "https" or parsed_url.netloc != parsed_base.netloc:
            raise FormaConfigurationError("Forma API URL має використовувати HTTPS і хост FORMA_API_BASE_URL")
        for attempt in range(3):
            self._throttle()
            try:
                with self._slots:
                    response = self._client.request(
                        method, url,
                        headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
                        json=json_body,
                    )
            except httpx.RequestError as exc:
                if attempt == 2:
                    raise FormaAPIError(f"Forma API недоступний: {type(exc).__name__}") from exc
                time.sleep(min(2 ** attempt, 4))
                continue
            if response.status_code == 401:
                # No documented login endpoint. A rotated env token can be picked up once.
                replacement = os.environ.get("FORMA_B2B_TOKEN", "")
                if attempt == 0 and replacement and replacement != self.token:
                    self.token = replacement
                    continue
                raise FormaAuthError("Forma API повернув 401; перевірте FORMA_B2B_TOKEN")
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < 2:
                    retry_after = response.headers.get("Retry-After", "")
                    wait = float(retry_after) if retry_after.replace(".", "", 1).isdigit() else 2 ** attempt
                    time.sleep(min(max(wait, 0), 30))
                    continue
                raise FormaAPIError(f"Forma API {response.status_code}: {urlparse(url).path}")
            if response.status_code >= 400:
                raise FormaAPIError(f"Forma API {response.status_code}: {urlparse(url).path}")
            try:
                return response.json()
            except ValueError as exc:
                raise FormaAPIError(f"Forma API повернув не-JSON: {urlparse(url).path}") from exc
        raise FormaAPIError("Forma API: вичерпано спроби")

    def get_category_tree(self):
        if self.category_tree_method not in {"GET", "POST"}:
            raise FormaConfigurationError("FORMA_CATEGORY_TREE_METHOD має бути GET або POST")
        body = None
        if self.category_tree_body:
            try:
                body = json.loads(self.category_tree_body)
            except ValueError as exc:
                raise FormaConfigurationError("FORMA_CATEGORY_TREE_BODY має бути JSON") from exc
        return self._request(self.category_tree_method, self.category_tree_url, json_body=body)

    def get_items_by_tree_id(self, tree_id: int):
        if isinstance(tree_id, bool) or not isinstance(tree_id, int) or tree_id <= 0:
            raise FormaConfigurationError("tree_id має бути додатним цілим числом")
        return self._request("POST", self.base_url + "/api/items/ByTreeId", json_body=tree_id)

    def get_item_vehicles(self, item_no: str):
        if not isinstance(item_no, str) or not item_no.strip():
            raise FormaConfigurationError("itemNo порожній")
        return self._request("POST", self.base_url + "/api/Catalog/ItemVehicles", json_body=item_no)

    @staticmethod
    def _image_url(path: str, base: str) -> str:
        parsed_base = urlparse(base)
        if parsed_base.scheme != "https" or not parsed_base.netloc:
            raise FormaConfigurationError("Forma image base URL має використовувати HTTPS")
        url = urljoin(base.rstrip("/") + "/", path.lstrip("/"))
        parsed_url = urlparse(url)
        if parsed_url.scheme != "https" or parsed_url.netloc != parsed_base.netloc:
            raise FormaConfigurationError("Forma photo URL має належати налаштованому хосту")
        return url

    def image_url(self, path: str) -> str:
        base = os.environ.get("FORMA_IMAGE_BASE_URL", "").strip() or DEFAULT_IMAGE_BASE_URL
        return self._image_url(path, base)

    def category_image_url(self, path: str) -> str:
        base = os.environ.get("FORMA_CATEGORY_IMAGE_BASE_URL", "").strip() or DEFAULT_CATEGORY_IMAGE_BASE_URL
        return self._image_url(path, base)

    def download_image(self, path: str, *, category=False) -> tuple[str, bytes, str]:
        url = self.category_image_url(path) if category else self.image_url(path)
        headers = {"Authorization": f"Bearer {self.token}"} if urlparse(url).netloc == urlparse(self.base_url).netloc else {}
        for attempt in range(3):
            self._throttle()
            try:
                with self._slots, self._client.stream(
                    "GET", url, headers=headers
                ) as response:
                    if response.status_code == 401:
                        raise FormaAuthError("Forma photo повернуло 401")
                    if response.status_code == 429 or response.status_code >= 500:
                        if attempt < 2:
                            time.sleep(2 ** attempt)
                            continue
                    if response.status_code != 200:
                        raise FormaAPIError(f"Forma photo HTTP {response.status_code}")
                    content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                    if content_type not in {"image/jpeg", "image/png", "image/webp"}:
                        raise FormaAPIError("Forma photo має непідтримуваний content-type")
                    chunks = []
                    size = 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > 8 * 1024 * 1024:
                            raise FormaAPIError("Forma photo перевищує 8 МБ")
                        chunks.append(chunk)
                    if not size:
                        raise FormaAPIError("Forma photo порожнє")
                    return url, b"".join(chunks), content_type
            except httpx.RequestError as exc:
                if attempt == 2:
                    raise FormaAPIError(f"Forma photo недоступне: {type(exc).__name__}") from exc
                time.sleep(2 ** attempt)
                continue
        raise FormaAPIError("Forma photo: вичерпано спроби")
