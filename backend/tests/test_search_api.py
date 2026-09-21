import uuid

import pytest
from rest_framework.test import APIClient

from apps.search import index

from .factories import make_category, make_generation, make_manufacturer, make_product


@pytest.fixture
def meili_index(settings):
    settings.MEILI_INDEX = f"test_products_{uuid.uuid4().hex[:8]}"
    try:
        index.ensure_settings()
    except Exception:
        pytest.skip("Meilisearch is not running")
    yield
    index.client().delete_index(settings.MEILI_INDEX)


@pytest.fixture
def catalog(db):
    optics = make_category("Оптика", "optika")
    headlights = make_category("Фари передні", "fary-perednie", parent=optics)
    body = make_category("Кузов", "kuzov")
    bumpers = make_category("Бампер, комплектуючі", "bamper-komplektuyushie", parent=body)
    passat = make_generation("Volkswagen", "Passat B7 USA", 2011, 2014)
    camry = make_generation("Toyota", "Camry 70", 2017, 2021)
    tyc, depo = make_manufacturer("TYC"), make_manufacturer("DEPO")
    items = {
        "passat_left": make_product(
            "Фара ліва передня Volkswagen Passat B7 USA 2010-2014", category=headlights, generations=[passat],
            numbers=["561941005D"], sku="FP7439R1T", manufacturer=tyc, side="left", price="4120",
        ),
        "passat_right": make_product(
            "Фара права передня Volkswagen Passat B7 USA 2010-2014", category=headlights, generations=[passat],
            numbers=["561941006D"], manufacturer=depo, side="right", price="3950",
        ),
        "camry_bumper": make_product(
            "Бампер передній Toyota Camry 70 2017-2021", category=bumpers, generations=[camry], price="5200",
        ),
        "camry_light": make_product(
            "Фара ліва Toyota Camry 70", category=headlights, generations=[camry], side="left", price="0",
        ),
    }
    return {**items, "passat": passat, "camry": camry, "headlights": headlights, "tyc": tyc}


def _api():
    return APIClient()


@pytest.mark.meili
@pytest.mark.django_db(transaction=True)
def test_human_query_finds_car_and_category(meili_index, catalog):
    index.reindex_all()
    body = _api().get("/api/search", {"q": "фара пасат б7"}).json()

    assert {r["id"] for r in body["results"]} == {catalog["passat_left"].id, catalog["passat_right"].id}
    assert body["understood"]["category"]["slug"] == "fary-perednie"
    assert body["understood"]["car"]["make"] == "Volkswagen"
    assert body["car_source"] == "query"
    assert body["degraded"] is False


@pytest.mark.meili
@pytest.mark.django_db(transaction=True)
def test_part_number_exact_first(meili_index, catalog):
    index.reindex_all()
    body = _api().get("/api/search/suggest", {"q": "5619 41005-d"}).json()

    assert body["kind"] == "part_number"
    assert body["products"][0]["id"] == catalog["passat_left"].id
    assert body["products"][0]["exact"] is True


@pytest.mark.meili
@pytest.mark.django_db(transaction=True)
def test_listing_with_my_car_and_facets(meili_index, catalog):
    index.reindex_all()
    body = _api().get("/api/products", {"category": "fary-perednie", "car": catalog["camry"].id}).json()

    assert [r["id"] for r in body["results"]] == [catalog["camry_light"].id]
    assert body["car_source"] == "my_car"

    all_cars = _api().get("/api/products", {"category": "fary-perednie", "car": catalog["camry"].id, "all_cars": 1}).json()
    assert all_cars["count"] == 3
    manufacturers = {m["name"]: m["count"] for m in all_cars["facets"]["manufacturers"]}
    assert manufacturers["DEPO"] == 1
    assert all_cars["facets"]["side"] == {"left": 2, "right": 1}

    filtered = _api().get("/api/products", {"category": "fary-perednie", "manufacturer": catalog["tyc"].id, "sort": "price_asc"}).json()
    prices = [r["price"] for r in filtered["results"]]
    assert prices[-1] == 0  # «ціну уточнюйте» goes last when sorting by price


@pytest.mark.meili
@pytest.mark.django_db(transaction=True)
def test_zero_results_relaxes_filters(meili_index, catalog):
    index.reindex_all()
    body = _api().get("/api/search", {"q": "бампер пасат"}).json()
    # no bumpers for Passat -> keep the car, drop the category
    assert body["relaxed"] is True
    assert body["count"] >= 1


@pytest.mark.django_db
def test_postgres_fallback_when_meili_down(monkeypatch, catalog):
    def down(*args, **kwargs):
        raise ConnectionError("meili down")

    monkeypatch.setattr(index, "multi_search", down)
    body = _api().get("/api/search", {"q": "фара пасат б7"}).json()

    assert body["degraded"] is True
    assert {r["id"] for r in body["results"]} == {catalog["passat_left"].id, catalog["passat_right"].id}
