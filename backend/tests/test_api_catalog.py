import pytest
from rest_framework.test import APIClient

from apps.content.models import Banner, Page

from .factories import make_category, make_generation, make_product, make_promotion

pytestmark = pytest.mark.django_db


@pytest.fixture
def api():
    return APIClient()


def test_home_has_all_sections(api):
    make_product(is_featured=True)
    Banner.objects.create(title="Розпродаж", placement="bento")

    body = api.get("/api/home").json()

    assert set(body) >= {"banners", "categories", "featured", "popular_makes", "promotions"}
    assert body["banners"]["bento"][0]["title"] == "Розпродаж"
    assert len(body["featured"]) == 1
    assert body["categories"][0]["children"][0]["product_count"] == 1


def test_product_detail_contains_fitments_and_sale_price(api):
    gen = make_generation()
    product = make_product(generations=[gen], numbers=["561941005D"], slug="fara-passat")
    make_promotion(15).products.add(product)

    body = api.get("/api/products/fara-passat").json()

    assert body["fitments"][0]["label"] == "Passat B7 USA (2011–2014)"
    assert body["fitments"][0]["make"] == "Volkswagen"
    assert body["sale_price"] == 2922
    assert body["discount_percent"] == 15
    assert {"number": "561941005D", "kind": "oem"} in body["part_numbers"]
    assert body["breadcrumbs"][-1]["name"] == "Фари передні"
    assert body["generation_ids"] == [gen.id]


def test_inactive_product_is_404(api):
    make_product(slug="hidden", is_active=False)
    assert api.get("/api/products/hidden").status_code == 404


def test_make_detail_groups_models_by_family(api):
    gen_usa = make_generation(model="Passat B7 USA")
    make_generation(model="Passat B7", year_from=2010, year_to=2015)
    make_generation(model="Golf 7", year_from=2012, year_to=2019)
    make_product(generations=[gen_usa])

    body = api.get("/api/makes/volkswagen").json()

    families = {f["family"]: f for f in body["families"]}
    assert set(families) == {"Passat", "Golf"}
    passat_models = {m["name"] for m in families["Passat"]["models"]}
    assert passat_models == {"Passat B7", "Passat B7 USA"}
    usa = next(m for m in families["Passat"]["models"] if m["name"] == "Passat B7 USA")
    assert usa["generations"][0]["product_count"] == 1


def test_generation_ref(api):
    gen = make_generation()
    body = api.get(f"/api/generations/{gen.id}").json()
    assert body == {
        "generation_id": gen.id,
        "make": "Volkswagen",
        "make_slug": "volkswagen",
        "model": "Passat B7 USA",
        "model_slug": "passat-b7-usa",
        "generation_slug": "2011-2014",
        "label": "Passat B7 USA (2011–2014)",
        "full_label": "Volkswagen Passat B7 USA (2011–2014)",
        "years_label": "2011–2014",
        "market": "usa",
    }


def test_car_page_lists_categories_with_counts(api):
    gen = make_generation()
    make_product(generations=[gen])
    make_product(generations=[gen])

    body = api.get("/api/cars/volkswagen/passat-b7-usa/2011-2014").json()

    assert body["full_label"] == "Volkswagen Passat B7 USA (2011–2014)"
    assert body["categories"] == [{"id": body["categories"][0]["id"], "slug": "fary-perednie", "name": "Фари передні", "count": 2}]


def test_legacy_resolve_mark_and_model(api):
    gen = make_generation(legacy_id="25714:24676")
    gen.model.make.legacy_id = 574
    gen.model.make.save()
    gen.model.legacy_id = 25714
    gen.model.save()

    assert api.get("/api/legacy/resolve", {"path": "/mark/574"}).json() == {"location": "/cars/volkswagen"}
    assert api.get("/api/legacy/resolve", {"path": "/model/574/25714/24676"}).json() == {
        "location": "/cars/volkswagen/passat-b7-usa/2011-2014"
    }
    assert api.get("/api/legacy/resolve", {"path": "/mark/1"}).status_code == 404


def test_category_detail_and_tree(api):
    make_product()
    tree = api.get("/api/categories").json()
    assert tree[0]["slug"] == "optika" and tree[0]["product_count"] == 1

    detail = api.get("/api/categories/fary-perednie").json()
    assert detail["parent"] == {"slug": "optika", "name": "Оптика"}


def test_settings_pages_and_banners(api):
    Page.objects.create(title="Доставка та оплата", slug="dostavka-ta-oplata", body="<p>НП</p>")
    Banner.objects.create(title="Хіт", placement="home_strip")

    assert api.get("/api/settings").json()["phones"][0]["label"] == "(063) 420-39-93"
    assert api.get("/api/pages").json()[0]["slug"] == "dostavka-ta-oplata"
    assert api.get("/api/pages/dostavka-ta-oplata").json()["body"] == "<p>НП</p>"
    assert api.get("/api/banners", {"placement": "home_strip"}).json()[0]["title"] == "Хіт"


def test_promotion_detail_lists_products(api):
    optics = make_category("Оптика", "optika")
    product = make_product()
    promo = make_promotion(10, slug="optika-10")
    promo.categories.add(optics)

    body = api.get("/api/promotions/optika-10").json()
    assert body["discount_percent"] == 10
    assert [p["id"] for p in body["products"]] == [product.id]
