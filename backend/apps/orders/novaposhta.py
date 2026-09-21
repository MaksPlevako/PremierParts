"""Nova Poshta directory lookups (cities, warehouses). Enabled only with NOVA_POSHTA_API_KEY."""

import httpx
from django.conf import settings
from django.core.cache import cache

API = "https://api.novaposhta.ua/v2.0/json/"


def enabled() -> bool:
    return bool(settings.NOVA_POSHTA_API_KEY)


def _call(model: str, method: str, props: dict) -> list[dict]:
    response = httpx.post(
        API,
        json={"apiKey": settings.NOVA_POSHTA_API_KEY, "modelName": model, "calledMethod": method, "methodProperties": props},
        timeout=6,
    )
    response.raise_for_status()
    body = response.json()
    return body.get("data") or []


def cities(query: str) -> list[dict]:
    key = f"np:cities:{query.lower()}"
    if (hit := cache.get(key)) is not None:
        return hit
    data = _call("Address", "searchSettlements", {"CityName": query, "Limit": "12", "Page": "1"})
    addresses = data[0].get("Addresses", []) if data else []
    result = [
        {"ref": a.get("DeliveryCity"), "name": a.get("Present") or a.get("MainDescription")}
        for a in addresses
        if a.get("DeliveryCity")
    ]
    cache.set(key, result, 3600)
    return result


def warehouses(city_ref: str, query: str = "") -> list[dict]:
    key = f"np:wh:{city_ref}:{query.lower()}"
    if (hit := cache.get(key)) is not None:
        return hit
    data = _call("Address", "getWarehouses", {"CityRef": city_ref, "FindByString": query, "Limit": "50", "Page": "1"})
    result = [{"ref": w.get("Ref"), "name": w.get("Description")} for w in data]
    cache.set(key, result, 3600)
    return result
