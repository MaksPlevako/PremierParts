"""Free NHTSA vPIC decoder (best coverage for North-American VINs)."""

import httpx
from django.conf import settings


def decode_values(vin: str, timeout: float = 4.0) -> dict | None:
    """Return the flat vPIC result row, or None when the service is unreachable."""
    try:
        response = httpx.get(settings.NHTSA_URL.format(vin=vin), timeout=timeout)
        response.raise_for_status()
        rows = response.json().get("Results") or []
    except (httpx.HTTPError, ValueError):
        return None
    return rows[0] if rows else None
