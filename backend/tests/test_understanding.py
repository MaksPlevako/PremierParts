import pytest

from apps.search.car_aliases import code_variants, translit_variants
from apps.search.understanding import understand

from .factories import make_category, make_generation

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalog():
    optics = make_category("Оптика", "optika")
    headlights = make_category("Фари передні", "fary-perednie", parent=optics)
    body = make_category("Кузов", "kuzov")
    bumpers = make_category("Бампер, комплектуючі", "bamper-komplektuyushie", parent=body)
    passat_usa = make_generation("Volkswagen", "Passat B7 USA", 2011, 2014)
    passat_eu = make_generation("Volkswagen", "Passat B7", 2010, 2015)
    passat_b6 = make_generation("Volkswagen", "Passat B6", 2005, 2010)
    camry70 = make_generation("Toyota", "Camry 70", 2017, 2021)
    camry50 = make_generation("Toyota", "Camry 50", 2011, 2014)
    return locals()


def test_translit_variants():
    assert {"пасат", "пассат"} <= translit_variants("passat")
    assert {"камрі", "камри"} <= translit_variants("camry")
    assert "акцент" in translit_variants("accent")
    assert "кашкай" in translit_variants("qashqai")


def test_code_variants():
    assert "b7" in code_variants("б7")
    assert "w124" in code_variants("в124")
    assert code_variants("b7") == {"b7"}


def test_empty(catalog):
    assert understand("   ").kind == "empty"


def test_vin(catalog):
    u = understand(" 1vwbp7a3xcc012345 ")
    assert u.kind == "vin"
    assert u.vin == "1VWBP7A3XCC012345"


@pytest.mark.parametrize("q", ["5619 41005-D", "561941005d", "FP7439-R1T", "A1248804070"])
def test_part_numbers(catalog, q):
    u = understand(q)
    assert u.kind == "part_number"
    assert u.part_number.isalnum() and u.part_number.isupper()


@pytest.mark.parametrize("q", ["golf 7 2015", "camry 70", "passat b7", "2015"])
def test_not_part_numbers(catalog, q):
    assert understand(q).kind == "text"


def test_human_text_with_car_and_category(catalog):
    u = understand("фара пасат б7")

    assert u.kind == "text"
    assert u.make_id == catalog["passat_usa"].model.make_id
    assert set(u.model_ids) == {catalog["passat_usa"].model_id, catalog["passat_eu"].model_id}
    assert u.category_id == catalog["headlights"].id
    assert u.text == ""


def test_latin_car_and_numeric_generation(catalog):
    u = understand("бампер camry 70")

    assert u.model_ids == [catalog["camry70"].model_id]
    assert u.category_id == catalog["bumpers"].id


def test_year_narrows_generations(catalog):
    u = understand("фара passat 2012")

    assert u.year == 2012
    assert set(u.generation_ids) == {catalog["passat_usa"].id, catalog["passat_eu"].id}


def test_side_and_leftover_text(catalog):
    u = understand("фара ліва passat b7 usa led")

    assert u.side == "left"
    assert u.model_ids == [catalog["passat_usa"].model_id]
    assert u.text == "led"


def test_make_only(catalog):
    u = understand("тойота")
    assert u.make_id == catalog["camry70"].model.make_id
    assert u.model_ids == []
