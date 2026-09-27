import json
from decimal import Decimal

import httpx
import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from apps.catalog.models import Category, Fitment, Generation, Make, Product
from apps.catalog.services.queries import category_counts, category_tree
from apps.forma.client import FormaAuthError, FormaClient, FormaConfigurationError
from apps.forma.images import needs_first_image, sync_first_image
from apps.forma.management.commands.forma_worker import claim_job, schedule_due_jobs
from apps.forma.models import (
    FormaAttributeName, FormaCategory, FormaItem, FormaItemAttribute,
    FormaSyncJob, FormaVehicleFitment, FormaVehicleType, FormaWarehouseStock,
)
from apps.forma.normalize import category_nodes, item_available, parse_stock, vehicle_key
from apps.forma.sync import run_sync_job
from apps.forma.upsert import ProductMatcher, sync_categories, upsert_item, upsert_vehicle_fitment
from apps.search.documents import load_products, product_document
from apps.search.service import Clause


TREE = [{
    "id": 788, "title": "Вихлопна система", "childElements": [
        {"id": 790, "parentId": 788, "title": "Труби", "itemGroup": "Вихлопна система", "childElements": []},
    ],
}]
ITEM = {
    "itemNo": "FP 0001 G135", "brand": "FPS", "description": "Труба 35 мм",
    "longText": "Опис товару", "price": 100.25, "retail": 150.75,
    "quantity": 0, "inStock": True,
    "stock": json.dumps({"Stock": [{"L": "КИЕВ1", "C": "КИЕВ1", "Q": ">3", "R": 0}]}),
    "criterias": [
        {"criteria": "ДІАМЕТР", "value": "35 ММ"},
        {"criteria": "діаметр", "value": "35 ММ"},
    ],
}
VEHICLE = {
    "mark": "ACURA", "model": "MDX", "typeId": 19000001,
    "typeName": "06-13", "typeRange": "", "fuel": None, "engineType": None,
}


def test_client_posts_raw_number_and_string_and_retries_429():
    seen = []

    def handler(request):
        seen.append(request)
        if len(seen) == 1:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200, json=[])

    with FormaClient(token="test-token", delay=0, transport=httpx.MockTransport(handler)) as client:
        assert client.get_items_by_tree_id(790) == []
        assert client.get_item_vehicles("FP 0001 G135") == []
    assert len(seen) == 3
    assert seen[0].content == b"790"
    assert seen[2].content == b'"FP 0001 G135"'
    assert all(request.headers["Authorization"] == "Bearer test-token" for request in seen)


def test_client_401_on_authenticated_endpoints():
    transport = httpx.MockTransport(lambda request: httpx.Response(401))
    with FormaClient(token="test-token", delay=0, transport=transport) as client:
        with pytest.raises(FormaAuthError):
            client.get_item_vehicles("FP 0001 G135")
        with pytest.raises(FormaAuthError):
            client.get_category_tree()


def test_client_uses_confirmed_catalog_post_by_default(monkeypatch):
    monkeypatch.delenv("FORMA_CATEGORY_TREE_URL", raising=False)
    monkeypatch.delenv("FORMA_CATEGORY_TREE_METHOD", raising=False)
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json=TREE)

    with FormaClient(token="test-token", delay=0, transport=httpx.MockTransport(handler)) as client:
        assert client.get_category_tree() == TREE
    assert seen[0].method == "POST"
    assert str(seen[0].url) == "https://ecom.ad.ua/api/content/Catalog"
    assert seen[0].content == b""


def test_client_uses_configured_tree_request():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json=TREE)

    with FormaClient(
        token="test-token", category_tree_url="https://ecom.ad.ua/verified/tree",
        category_tree_method="POST", category_tree_body='{"scope":"all"}',
        delay=0, transport=httpx.MockTransport(handler),
    ) as client:
        assert client.get_category_tree() == TREE
    assert seen[0].method == "POST"
    assert json.loads(seen[0].content) == {"scope": "all"}
    with FormaClient(
        token="test-token", category_tree_url="https://unrelated.example/tree",
        delay=0, transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(FormaConfigurationError, match="FORMA_API_BASE_URL"):
            client.get_category_tree()


def test_image_url_requires_confirmed_host(monkeypatch):
    monkeypatch.setenv("FORMA_IMAGE_BASE_URL", "https://images.forma.example/media/")
    with FormaClient(token="test-token", delay=0) as client:
        assert client.image_url("tcd-com/19000/a.jpg?1") == "https://images.forma.example/media/tcd-com/19000/a.jpg?1"
        with pytest.raises(FormaConfigurationError):
            client.image_url("https://unrelated.example/secret.jpg")


def test_image_url_defaults_to_confirmed_product_host(monkeypatch):
    monkeypatch.delenv("FORMA_IMAGE_BASE_URL", raising=False)
    monkeypatch.delenv("FORMA_CATEGORY_IMAGE_BASE_URL", raising=False)
    with FormaClient(token="test-token", delay=0) as client:
        assert client.image_url("tcd-com/19000/0001G145.jpg?46290203") == (
            "https://img2.ad.ua/imgs/tcd-com/19000/0001G145.jpg?46290203"
        )
        assert client.image_url("/tcd-com/19/MR/MRVI0052.jpg?46290203") == (
            "https://img2.ad.ua/imgs/tcd-com/19/MR/MRVI0052.jpg?46290203"
        )
        assert client.category_image_url("19/540.jpg") == "https://img2.ad.ua/imgs/group-pic/19/540.jpg"


def test_nested_tree_stock_and_vehicle_normalization():
    nodes = list(category_nodes(TREE))
    assert [(node["id"], parent, leaf) for node, parent, _, leaf in nodes] == [
        (788, None, False), (790, 788, True),
    ]
    stock = parse_stock(ITEM["stock"])
    assert stock[0].quantity_raw == ">3"
    assert stock[0].quantity_min == 4
    assert stock[0].more_than is True
    assert item_available(ITEM, stock) is True
    assert vehicle_key(VEHICLE) == "id:19000001"
    assert vehicle_key({"mark": " Acura ", "model": " MDX ", "typeName": "06-13", "typeId": 0}) == vehicle_key(
        {"mark": "ACURA", "model": "mdx", "typeName": "06-13", "typeId": 0}
    )


@pytest.mark.django_db
def test_repeated_item_stock_attributes_and_vehicle_upsert(client):
    category = sync_categories(TREE)[0]
    matcher = ProductMatcher()
    item, created = upsert_item(ITEM, category, matcher)
    assert created is True
    assert item.product.price == Decimal("150.75")
    assert item.product.supplier_price is None
    assert item.supplier_customer_price == Decimal("100.25")
    assert item.product.stock_status == "in_stock"
    assert FormaWarehouseStock.objects.get(item=item).quantity_min == 4
    assert FormaAttributeName.objects.count() == 1
    assert FormaItemAttribute.objects.get(item=item).value == "35 ММ"

    assert upsert_vehicle_fitment(item, VEHICLE) is True
    assert upsert_vehicle_fitment(item, {**VEHICLE, "mark": "Acura", "fuel": None}) is False
    assert Make.objects.filter(name__iexact="ACURA").count() == 1
    assert Generation.objects.count() == 1
    assert Generation.objects.get().years_label == ""
    assert Generation.objects.get().source_label == "06-13"
    assert Fitment.objects.count() == FormaVehicleFitment.objects.count() == 1
    detail = client.get(f"/api/products/{item.product.slug}").json()
    assert detail["attributes"] == [{"name": "ДІАМЕТР", "value": "35 ММ"}]
    assert detail["fitments"][0]["type_label"] == "06-13"

    updated = {**ITEM, "retail": "160.00", "inStock": False, "stock": '{"Stock":[]}', "criterias": []}
    again, created_again = upsert_item(updated, category, matcher)
    assert created_again is False
    assert again.pk == item.pk
    assert Product.objects.count() == FormaItem.objects.count() == 1
    assert Product.objects.get().price == Decimal("160.00")
    assert Product.objects.get().stock_status == "out_of_stock"
    assert FormaWarehouseStock.objects.count() == FormaItemAttribute.objects.count() == 0
    assert client.get(f"/api/products/{item.product.slug}").json()["attributes"] == []
    upsert_item({**updated, "retail": 0}, category, matcher)
    assert Product.objects.get().price == 0


@pytest.mark.django_db
def test_full_then_fast_sync_is_idempotent(monkeypatch):
    indexed = []
    monkeypatch.setattr("apps.forma.sync.search_index.upsert_products", lambda ids: indexed.extend(ids))
    class FakeClient:
        concurrency = 2
        item = ITEM

        def get_items_by_tree_id(self, tree_id):
            assert tree_id == 790
            return [self.item]

        def get_item_vehicles(self, item_no):
            return [VEHICLE]

    fake_client = FakeClient()
    full = FormaSyncJob.objects.create(mode="full")
    run_sync_job(full, client=fake_client, category_tree=TREE)
    assert full.status == "completed"
    assert full.products_created == full.fitments_created == 1
    assert indexed == [FormaItem.objects.get().product_id]
    fake_client.item = {**ITEM, "retail": 175, "description": "Changed only in fast", "criterias": []}
    fast = FormaSyncJob.objects.create(mode="fast")
    run_sync_job(fast, client=fake_client)
    assert fast.status == "completed"
    assert fast.products_created == 0
    assert Product.objects.get().price == Decimal("175.00")
    assert Product.objects.get().name == ITEM["description"]
    assert FormaItemAttribute.objects.count() == 1
    assert (Category.objects.count(), Product.objects.count(), FormaVehicleType.objects.count(), Fitment.objects.count()) == (2, 1, 1, 1)
    root_id = FormaCategory.objects.get(external_id=788).category_id
    assert category_counts()[root_id] == 1


@pytest.mark.django_db
def test_empty_vehicles_and_missing_photo_do_not_break_full_sync(monkeypatch):
    monkeypatch.setattr("apps.forma.sync.search_index.upsert_products", lambda ids: None)
    class FakeClient:
        concurrency = 1

        def get_items_by_tree_id(self, tree_id):
            return [{**ITEM, "firstPic": ""}]

        def get_item_vehicles(self, item_no):
            return []

    job = FormaSyncJob.objects.create(mode="full")
    run_sync_job(job, client=FakeClient(), category_tree=TREE)
    assert job.status == "completed"
    assert job.vehicles_processed == 0
    assert FormaVehicleFitment.objects.count() == 0


@pytest.mark.django_db
def test_photo_downloaded_once_into_server_storage(tmp_path, settings, monkeypatch):
    settings.MEDIA_ROOT = tmp_path
    monkeypatch.setenv("FORMA_IMAGE_BASE_URL", "https://images.forma.example/media/")
    category = sync_categories(TREE)[0]
    item, _ = upsert_item({**ITEM, "firstPic": "tcd-com/19000/a.jpg?1"}, category, ProductMatcher())
    calls = []

    def image_response(request):
        calls.append(request)
        return httpx.Response(200, headers={"content-type": "image/jpeg"}, content=b"example-photo")

    with FormaClient(token="test-token", delay=0, transport=httpx.MockTransport(image_response)) as client:
        assert needs_first_image(item, client)
        assert sync_first_image(item, client)
        assert not needs_first_image(item, client)
        assert not sync_first_image(item, client)
    assert len(calls) == 1
    assert "Authorization" not in calls[0].headers
    assert item.product.images.count() == 1
    assert item.product.images.first().image.name.startswith("products/forma/")


@pytest.mark.django_db
def test_full_sync_downloads_category_image_once(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    tree = [
        {"id": 540, "title": "Автомобільне кріплення", "img": "19/540.jpg", "childElements": []},
        {"id": 541, "title": "Інша категорія", "img": "19/541.jpg", "childElements": []},
    ]

    class FakeClient:
        concurrency = 1
        downloads = 0

        def get_items_by_tree_id(self, tree_id):
            return []

        def category_image_url(self, path):
            return "https://img2.ad.ua/imgs/group-pic/" + path

        def download_image(self, path, *, category=False):
            assert category is True
            self.downloads += 1
            return self.category_image_url(path), b"category-photo", "image/jpeg"

    client = FakeClient()
    for _ in range(2):
        job = FormaSyncJob.objects.create(mode="full")
        run_sync_job(job, client=client, category_tree=tree, category_ids=[540])
        assert job.status == "completed"
    assert client.downloads == 1
    category = FormaCategory.objects.get(external_id=540).category
    assert category.image.name.startswith("categories/forma/")
    assert not FormaCategory.objects.get(external_id=541).category.image


@pytest.mark.django_db
def test_admin_can_queue_job_and_worker_claims_it(client, monkeypatch):
    monkeypatch.setenv("FORMA_AUTOSYNC", "false")
    admin = User.objects.create_superuser("forma-admin", "forma-admin@example.com", "pass12345")
    client.force_login(admin)
    url = reverse("admin:forma_formasyncjob_add")
    assert client.get(url).status_code == 200
    response = client.post(url, {"mode": "fast", "_save": "Save"})
    assert response.status_code == 302
    job = FormaSyncJob.objects.get()
    assert job.mode == "fast"
    assert job.requested_by == admin
    assert client.get(reverse("admin:forma_formasyncjob_changelist")).status_code == 200
    assert client.get(reverse("admin:forma_formasyncjob_change", args=[job.pk])).status_code == 200
    assert claim_job().pk == job.pk
    assert claim_job() is None


@pytest.mark.django_db
def test_scheduler_queues_full_with_confirmed_catalog_endpoint(monkeypatch):
    monkeypatch.setenv("FORMA_AUTOSYNC", "true")
    monkeypatch.setenv("FORMA_B2B_TOKEN", "test-token")
    monkeypatch.delenv("FORMA_CATEGORY_TREE_URL", raising=False)
    schedule_due_jobs()
    assert list(FormaSyncJob.objects.values_list("mode", flat=True)) == ["full"]


@pytest.mark.django_db
def test_category_count_reaches_all_ancestors():
    tree = [{"id": 1, "title": "Root", "childElements": [
        {"id": 2, "title": "Middle", "childElements": [
            {"id": 3, "title": "Leaf", "childElements": []},
        ]},
    ]}]
    leaf = sync_categories(tree)[0]
    upsert_item(ITEM, leaf, ProductMatcher())
    counts = category_counts()
    assert [counts[FormaCategory.objects.get(external_id=external_id).category_id] for external_id in (1, 2, 3)] == [1, 1, 1]
    root = category_tree()[0]
    assert root["children"][0]["children"][0]["name"] == "Leaf"
    assert root["children"][0]["children"][0]["product_count"] == 1
    product = Product.objects.get()
    [loaded] = load_products([product.id])
    document = product_document(loaded, [])
    assert document["category_ids"] == [
        FormaCategory.objects.get(external_id=external_id).category_id for external_id in (3, 2, 1)
    ]
    category_map = {
        category_id: (parent_id, name)
        for category_id, parent_id, name in Category.objects.values_list("id", "parent_id", "name")
    }
    assert product_document(loaded, [], category_map)["category_ids"] == document["category_ids"]
    root_id = FormaCategory.objects.get(external_id=1).category_id
    assert Product.objects.filter(Clause("category_ids", "=", root_id).django()).count() == 1


@pytest.mark.django_db
def test_confirmed_forma_catalog_tree_preserves_sort_and_image_path():
    tree = [{
        "comId": 19, "sort": 4, "id": 540, "parentId": 0,
        "active": True, "img": "19/540.jpg", "title": "Автомобільне кріплення",
        "childElements": [{
            "comId": 19, "sort": 10, "id": 559, "parentId": 540,
            "active": True, "img": "19/559.jpg", "title": "Автомобільне кріплення",
            "childElements": [{
                "comId": 19, "sort": 3, "id": 560, "parentId": 559,
                "active": True, "img": "19/560.jpg", "title": "Елементи кріплення",
                "itemGroup": "Автокріплення", "itemSubGroup": "Елементи кріплення",
                "childElements": [],
            }],
        }],
    }]
    leaves = sync_categories(tree)
    assert [leaf.external_id for leaf in leaves] == [560]
    root = FormaCategory.objects.get(external_id=540)
    middle = FormaCategory.objects.get(external_id=559)
    leaf = leaves[0]
    assert (root.category.sort, middle.category.sort, leaf.category.sort) == (4, 10, 3)
    assert leaf.category.parent_id == middle.category_id
    assert middle.category.parent_id == root.category_id
    assert leaf.source_image_path == "19/560.jpg"
    assert leaf.item_group == "Автокріплення"
