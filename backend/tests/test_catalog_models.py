import pytest

from apps.catalog.models import CarModel, Category, Generation, Make, Market, PartNumber, Product


@pytest.mark.parametrize(
    "name, family",
    [
        ("Passat B7 USA", "Passat"),
        ("Elantra AD", "Elantra"),
        ("Grand Vitara", "Grand Vitara"),
        ("Corolla E150", "Corolla"),
        ("3 Series E90", "3 Series"),
        ("6 GJ", "6"),
        ("CR-V", "CR-V"),
    ],
)
def test_derive_family(name, family):
    assert CarModel.derive_family(name) == family


@pytest.mark.parametrize(
    "name, market",
    [("Passat B7 USA", Market.USA), ("Camry 50 EU", Market.EU), ("Accent", Market.OTHER)],
)
def test_derive_market(name, market):
    assert CarModel.derive_market(name) == market


@pytest.mark.django_db
def test_generation_labels():
    make = Make.objects.create(name="Volkswagen", slug="volkswagen")
    model = CarModel.objects.create(make=make, name="Passat B7 USA", slug="passat-b7-usa")
    closed = Generation.objects.create(model=model, year_from=2011, year_to=2014, slug="2011-2014")
    open_ended = Generation(model=model, year_from=2018, year_to=None)
    no_years = Generation(model=model)

    assert closed.years_label == "2011–2014"
    assert closed.label == "Passat B7 USA (2011–2014)"
    assert closed.full_label == "Volkswagen Passat B7 USA (2011–2014)"
    assert open_ended.years_label == "2018–"
    assert no_years.label == "Passat B7 USA"
    assert closed.covers_year(2012) and not closed.covers_year(2015)
    assert open_ended.covers_year(2030)
    assert no_years.covers_year(1999)


@pytest.mark.django_db
def test_part_number_is_normalized_on_save():
    category = Category.objects.create(name="Фари передні", slug="fary-perednie")
    product = Product.objects.create(name="Фара", slug="fara", category=category)
    pn = PartNumber.objects.create(product=product, number="5619 41005-d", kind="oem")

    assert pn.normalized == "561941005D"


@pytest.mark.django_db
def test_carmodel_fills_family_and_market_on_save():
    make = Make.objects.create(name="Volkswagen", slug="volkswagen")
    model = CarModel.objects.create(make=make, name="Passat B7 USA", slug="passat-b7-usa")

    assert model.family == "Passat"
    assert model.market == Market.USA
