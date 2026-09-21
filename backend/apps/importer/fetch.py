"""Polite HTTP client for the legacy site: disk cache, retries, bounded concurrency."""

import hashlib
import logging
import threading
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import httpx

log = logging.getLogger(__name__)
USER_AGENT = "PremierPartsImporter/1.0 (+https://premier-parts.com.ua; site owner migration)"


class Fetcher:
    def __init__(self, cache_dir: Path, concurrency: int = 4, delay: float = 0.25, timeout: float = 20):
        self.cache_dir = Path(cache_dir)
        (self.cache_dir / "html").mkdir(parents=True, exist_ok=True)
        self.concurrency = concurrency
        self.delay = delay
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=timeout, follow_redirects=True
        )
        self._lock = threading.Lock()
        self._last = 0.0

    def _throttle(self) -> None:
        with self._lock:
            wait = self._last + self.delay / max(self.concurrency, 1) - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()

    def _request(self, url: str) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(3):
            self._throttle()
            try:
                response = self._client.get(url)
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError("server error", request=response.request, response=response)
                return response
            except httpx.HTTPError as exc:
                last_exc = exc
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"GET {url} failed: {last_exc}")

    def get(self, url: str) -> str:
        path = self.cache_dir / "html" / (hashlib.sha1(url.encode()).hexdigest() + ".html")
        if path.exists():
            return path.read_text(encoding="utf-8")
        response = self._request(url)
        response.raise_for_status()
        html = response.text
        path.write_text(html, encoding="utf-8")
        return html

    def download(self, url: str, dest_dir: Path) -> Path | None:
        dest_dir.mkdir(parents=True, exist_ok=True)
        name = Path(urlparse(url).path).name or hashlib.sha1(url.encode()).hexdigest() + ".jpg"
        dest = dest_dir / name
        if dest.exists() and dest.stat().st_size > 0:
            return dest
        try:
            response = self._request(url)
        except RuntimeError as exc:
            log.warning("%s", exc)
            return None
        if response.status_code != 200 or not response.headers.get("content-type", "").startswith("image/"):
            return None
        dest.write_bytes(response.content)
        return dest

    def map(self, items: Iterable, fn: Callable, on_error: Callable | None = None) -> list:
        results = []
        with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
            futures = {pool.submit(fn, item): item for item in items}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as exc:
                    if on_error:
                        on_error(futures[future], exc)
                    else:
                        log.warning("task %s failed: %s", futures[future], exc)
        return results
