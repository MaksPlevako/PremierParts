"""Tell Next.js to drop cached pages (on-demand ISR) after admin edits."""

import logging
import threading
from contextlib import contextmanager

import httpx
from django.conf import settings
from django.db import transaction

log = logging.getLogger(__name__)
_state = threading.local()


@contextmanager
def suppress_revalidation():
    """Bulk jobs (import, reindex) revalidate once at the end instead of per row."""
    previous = getattr(_state, "suppressed", False)
    _state.suppressed = True
    try:
        yield
    finally:
        _state.suppressed = previous


def is_suppressed() -> bool:
    return getattr(_state, "suppressed", False)


def _send(tags: list[str]) -> None:
    url = settings.NEXT_REVALIDATE_URL
    if not url:
        return
    try:
        httpx.post(url, json={"tags": tags}, headers={"x-revalidate-secret": settings.REVALIDATE_SECRET}, timeout=2)
    except Exception as exc:  # the site must keep working even if Next is down
        log.warning("revalidate %s failed: %s", tags, exc)


def _dispatch(tags: list[str]) -> None:
    if getattr(settings, "REVALIDATE_ASYNC", True):
        # never make an admin save wait for Next.js (DNS/timeouts when the frontend is down)
        threading.Thread(target=_send, args=(tags,), daemon=True).start()
    else:
        _send(tags)


def revalidate_tags(tags: list[str], *, immediate: bool = False) -> None:
    if getattr(_state, "suppressed", False):
        return
    unique = list(dict.fromkeys(tags))
    if immediate:
        _send(unique)
    else:
        transaction.on_commit(lambda: _dispatch(unique))
