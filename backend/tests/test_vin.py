from datetime import date

import httpx
import pytest
from rest_framework.test import APIClient

from apps.vin import decoder, nhtsa
from apps.vin.decoder import VinError, check_digit_ok, model_year, validate_vin
from apps.vin.matching import match_generations
from apps.vin.models import VinRequest, Wmi

from .factories import make_generation

NHTSA_PASSAT = {
    "Count": 1,
    "Results": [
        {
            "Make": "VOLKSWAGEN",
            "Model": "Passat",
            "Series": "",
            "ModelYear": "2012",
            "BodyClass": "Sedan/Saloon",
            "DisplacementL": "2.5",
            "PlantCountry": "UNITED STATES (USA)",
            "ErrorCode": "0",
        }
    ],
}


def test_check_digit():
    assert check_digit_ok("1M8GDM9AXKP042788")
    assert not check_digit_ok("1M8GDM9A1KP042788")


def test_model_year_north_america_uses_position_7():
    assert model_year("1VWBP7A3XCC012345") == 2012
    assert model_year("1M8GDM9AXKP042788") == 1989


def test_model_year_rest_of_world_picks_latest_past_year():
    assert model_year("WVWZZZ3CZBE012345", today=date(2026, 9, 21)) == 2011
    assert model_year("WVWZZZ3CZYE012345", today=date(2026, 9, 21)) == 2000


def test_validate_vin_rejects_bad_input():
    with pytest.raises(VinError):
        validate_vin("1VWBP7A3XCC01234")  # 16 chars
    with pytest.raises(VinError):
        validate_vin("1VWBP7A3XCC0I2345")  # letter I is not allowed
    vin, warnings = validate_vin(" 1vwbp7a3xcc012345 ")
    assert vin == "1VWBP7A3XCC012345"
    assert warnings  # made-up VIN has a wrong check digit


@pytest.mark.django_db
def test_decode_uses_nhtsa_and_caches(monkeypatch):
    Wmi.objects.create(code="1VW", make_name="Volkswagen", country="США")
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        return httpx.Response(200, json=NHTSA_PASSAT, request=httpx.Request("GET", url))

    monkeypatch.setattr(nhtsa.httpx, "get", fake_get)
    info = decoder.decode("1VWBP7A3XCC012345")
    again = decoder.decode("1VWBP7A3XCC012345")

    assert (info.make, info.model, info.year, info.market, info.source) == ("Volkswagen", "Passat", 2012, "usa", "nhtsa")
    assert again.model == "Passat"
    assert len(calls) == 1


@pytest.mark.django_db
def test_decode_falls_back_to_wmi_on_timeout(monkeypatch):
    Wmi.objects.create(code="WVW", make_name="Volkswagen", country="Німеччина")

    def boom(url, timeout):
        raise httpx.ConnectTimeout("slow")

    monkeypatch.setattr(nhtsa.httpx, "get", boom)
    info = decoder.decode("WVWZZZ3CZBE012345")

    assert info.source == "wmi"
    assert info.make == "Volkswagen"
    assert info.year == 2011
    assert info.country == "Німеччина"


@pytest.mark.django_db
def test_match_prefers_usa_generation_for_us_vin():
    usa = make_generation("Volkswagen", "Passat B7 USA", 2011, 2014)
    eu = make_generation("Volkswagen", "Passat B7", 2010, 2015)
    make_generation("Volkswagen", "Passat B6", 2005, 2010)

    info = decoder.VinInfo(vin="1VWBP7A3XCC012345", make="Volkswagen", model="Passat", year=2012, market="usa", source="nhtsa")
    matches = match_generations(info)

    assert [g.id for g in matches] == [usa.id, eu.id]


@pytest.mark.django_db
def test_vin_api(monkeypatch):
    make_generation("Volkswagen", "Passat B7 USA", 2011, 2014)
    Wmi.objects.create(code="1VW", make_name="Volkswagen", country="США")
    monkeypatch.setattr(
        nhtsa.httpx, "get", lambda url, timeout: httpx.Response(200, json=NHTSA_PASSAT, request=httpx.Request("GET", url))
    )
    api = APIClient()

    body = api.post("/api/vin/decode", {"vin": "1VWBP7A3XCC012345"}, format="json").json()
    assert body["make"] == "Volkswagen" and body["year"] == 2012
    assert body["matches"][0]["label"] == "Passat B7 USA (2011–2014)"

    assert api.post("/api/vin/decode", {"vin": "123"}, format="json").status_code == 400

    created = api.post(
        "/api/vin/requests",
        {"vin": "1VWBP7A3XCC012345", "name": "Олег", "phone": "063 420 39 93", "part_query": "Фара ліва"},
        format="json",
    )
    assert created.status_code == 201
    req = VinRequest.objects.get()
    assert req.phone == "+380634203993"
    assert req.decoded["make"] == "Volkswagen"
