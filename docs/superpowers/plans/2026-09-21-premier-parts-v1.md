# Premier Parts V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Локальне демо преміального інтернет-магазину Premier Parts: каталог, розумний пошук (VIN / номер / текст), «Моє авто», кошик і замовлення, адмінка з редагуванням усього контенту.

**Architecture:** Next.js 16 (App Router, серверні компоненти, ISR з тегами) читає Django REST API; Django 5.2 + Unfold — адмінка і джерело правди в Postgres; Meilisearch — індекс пошуку й фасетів; усе за Nginx в одному Docker Compose.

**Tech Stack:** Next.js 16, React 19, TypeScript strict, Tailwind CSS 4, Motion 12, anime.js 4, next-intl 4, zustand, zod · Python 3.13, Django 5.2 LTS, DRF 3.16+, django-unfold, django-modeltranslation, django-import-export, meilisearch-python, httpx, beautifulsoup4, pytest-django · PostgreSQL 17, Meilisearch 1.54, Nginx 1.27.

**Spec:** `docs/superpowers/specs/2026-09-21-premier-parts-v1-design.md`

## Global Constraints

- Мова інтерфейсу: лише українська (`uk`), але всі тексти UI — через next-intl (`messages/uk.json`), всі контентні поля моделей — через modeltranslation (`LANGUAGES = [("uk", "Українська")]`, `MODELTRANSLATION_DEFAULT_LANGUAGE = "uk"`).
- Кольори: графіт `#15181C`; платина `#EEF0F2`/`#F7F8F9`/`#E1E4E8`; золотий градієнт `#9C7424 → #E7C573 → #F7E6B0 → #B98E3A`; золото не використовується для основного тексту.
- Шрифти: Unbounded (заголовки, ціни), Onest (текст), subsets `cyrillic`, `latin`.
- Валюта: гривня, формат `3 438 ₴` (нерозривний пробіл тисяч, `Intl.NumberFormat('uk-UA')`); ціна 0 = «Ціну уточнюйте».
- Контакти за замовчуванням (seed): `(063) 420-39-93` (Viber), `(098) 070-14-34`, `info@premier-parts.com.ua`, «Київ, вул. Вікентія Беретті, 6Б», Пн–Пт 10:00–18:00.
- Legacy URL зберігаються: `/product/<slug>`, `/category/<slug>`, `/page/<slug>`; `/mark/<id>` і `/model/<m>/<mo>/<s>` → 301.
- Усе запускається `docker compose up`; сайт на `http://localhost:8080`, адмінка `http://localhost:8080/admin`.
- Анімації поважають `prefers-reduced-motion`.
- Кожен task закінчується зеленими тестами і комітом (`Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`).

---

## Файлова структура

```
docker-compose.yml, .env.example, nginx/default.conf, README.md
backend/
  Dockerfile, pyproject.toml (deps), pytest.ini, manage.py
  config/{settings.py, urls.py, wsgi.py}
  apps/core/        normalize.py (normalize_part_number, slugify_uk), revalidate.py (Next revalidation), pagination.py
  apps/catalog/     models.py, translation.py, admin.py, serializers.py, views.py, urls.py, services/pricing.py, services/queries.py, signals.py
  apps/content/     models.py, translation.py, admin.py, serializers.py, views.py, urls.py
  apps/search/      models.py (SearchSynonym), documents.py (product → doc), index.py (Meili client, settings, sync), understanding.py (classify/parse query), car_aliases.py, views.py, urls.py, signals.py, management/commands/reindex_search.py
  apps/vin/         models.py, decoder.py, nhtsa.py, matching.py, fixtures/wmi.json, views.py, urls.py, management/commands/load_wmi.py
  apps/orders/      models.py, services.py (create_order, create_quick_order), notify.py, serializers.py, views.py, urls.py, admin.py, novaposhta.py
  apps/importer/    fetch.py (кеш-клієнт), parsers.py (чисті функції HTML → dataclass), loader.py (upsert у БД), management/commands/{import_premier.py, seed_demo.py}
  apps/dashboard/   unfold dashboard callback
  tests/            fixtures/*.html + test_*.py по модулях
frontend/
  Dockerfile, package.json, next.config.ts, tsconfig.json, eslint.config.mjs, vitest.config.ts, playwright.config.ts
  messages/uk.json
  src/i18n/{routing.ts, request.ts, navigation.ts}
  src/proxy.ts (next-intl + legacy redirects; у Next 16 middleware.ts → proxy.ts)
  src/app/[locale]/... сторінки; src/app/api/revalidate/route.ts; src/app/sitemap.ts; src/app/robots.ts
  src/lib/{api.ts, types.ts, format.ts, vin.ts, car-cookie.ts, seo.ts}
  src/stores/{cart.ts, my-car.ts}
  src/components/{brand,layout,search,car,product,catalog,home,cart,checkout,ui}/...
```

---

## Фаза A — Інфраструктура та ядро бекенду

### Task A1: Каркас Docker Compose + Django + Postgres + Meilisearch + Nginx

**Files:** Create `docker-compose.yml`, `.env.example`, `nginx/default.conf`, `backend/Dockerfile`, `backend/pyproject.toml`, `backend/manage.py`, `backend/config/*`, `backend/pytest.ini`, `backend/tests/test_health.py`, `backend/apps/core/{__init__,apps,views,urls}.py`

**Interfaces — Produces:** `GET /api/health` → `{"status":"ok","db":true,"search":bool}`; env vars `DJANGO_SECRET_KEY, DATABASE_URL, MEILI_URL, MEILI_MASTER_KEY, NEXT_REVALIDATE_URL, REVALIDATE_SECRET, NOVA_POSHTA_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID`.

- [ ] Step 1: тест `test_health` (клієнт DRF → 200, `status == "ok"`, `db is True`).
- [ ] Step 2: запустити — FAIL (немає проєкту).
- [ ] Step 3: створити Django-проєкт: settings читають env; `INSTALLED_APPS` з `unfold` (перед `django.contrib.admin`), `modeltranslation` (перед admin), `rest_framework`, `django_filters`, `import_export`, apps.*; `LANGUAGE_CODE="uk"`, `TIME_ZONE="Europe/Kyiv"`; `MEDIA_ROOT=/data/media`; `SERVE_MEDIA=True` → `django.views.static.serve` для `/media/`. Health view перевіряє `connection.ensure_connection()` і `meili.health()` (try/except → False).
- [ ] Step 4: compose: `postgres:17-alpine` (volume, healthcheck), `getmeili/meilisearch:v1.54` (`MEILI_ENV=development`, master key), `backend` (gunicorn `config.wsgi` 3 workers, volume `media`), `frontend`, `nginx:1.27-alpine` (порт 8080; `/api/ /admin/ /static/` → backend; `/media/` → alias volume; `/` → frontend з upgrade headers).
- [ ] Step 5: `docker compose up -d postgres meilisearch backend` + `docker compose exec backend pytest tests/test_health.py` — PASS.
- [ ] Step 6: commit `feat: docker compose skeleton with django, postgres, meilisearch`.

### Task A2: Нормалізація номерів і slug

**Files:** Create `backend/apps/core/normalize.py`, `backend/tests/test_normalize.py`

**Interfaces — Produces:** `normalize_part_number(raw: str) -> str`; `slugify_uk(text: str) -> str` (транслітерація за КМУ-2010, lower, дефіси); `split_part_numbers(text: str) -> list[str]` (витягує кандидати-номери з рядка: токени ≥5 символів з цифрою).

- [ ] Step 1: тести:
```python
from apps.core.normalize import normalize_part_number, slugify_uk, split_part_numbers
def test_normalize_strips_separators_and_case():
    assert normalize_part_number(" 5619 41005-d ") == "561941005D"
    assert normalize_part_number("fp7439-r1t") == "FP7439R1T"
    assert normalize_part_number("A 124 880 40 70") == "A1248804070"
def test_slugify_uk():
    assert slugify_uk("Фари передні") == "fary-peredni"
    assert slugify_uk("Volkswagen Passat B7 USA") == "volkswagen-passat-b7-usa"
def test_split_part_numbers():
    assert split_part_numbers("Фара ліва Volkswagen Passat B7 USA 2010-2014 (561941005D)") == ["561941005D"]
    assert split_part_numbers("GHK151160 GHK151160A") == ["GHK151160", "GHK151160A"]
```
- [ ] Step 2: FAIL. Step 3: реалізувати (регекс `[^A-Z0-9]` після upper; `split_part_numbers` ігнорує роки `^(19|20)\d{2}$` і діапазони `2010-2014`). Step 4: PASS. Step 5: commit.

### Task A3: Моделі каталогу + переклади + адмінка Unfold

**Files:** Create `backend/apps/catalog/{models,translation,admin,apps}.py`, migration; `backend/tests/test_catalog_models.py`

**Interfaces — Produces (models):**
- `Make(name, slug, logo, is_popular, sort, legacy_id:int|None)`
- `CarModel(make FK related_name="models", name, family, slug, legacy_id)`; `family` — базова назва («Passat B7 USA» → «Passat»), обчислюється `CarModel.derive_family(name)`.
- `Generation(model FK related_name="generations", year_from:int|None, year_to:int|None, market: "eu"|"usa"|"asia"|"other", slug, legacy_id:str "<model_legacy>:<series_legacy>")`; властивості `years_label` («2011–2014», «2018–», «»), `label` («Passat B7 USA (2011–2014)»), `full_label` («Volkswagen Passat B7 USA (2011–2014)»); `covers_year(y) -> bool`.
- `Category(parent FK null related_name="children", name*, slug unique, icon: str, image, sort, description*)`
- `Manufacturer(name unique, slug, logo, country)`
- `Product(name*, slug unique, sku, manufacturer FK null, category FK, description*, price Decimal(10,2) default 0, old_price null, stock_status, side, position, condition="new", is_active, is_featured, popularity, legacy_url unique null, created_at, updated_at)`
- `ProductImage(product FK related_name="images", image, alt, sort)`
- `Fitment(product FK related_name="fitments", generation FK related_name="fitments")` unique together
- `PartNumber(product FK related_name="part_numbers", number, normalized db_index, kind "sku"|"oem"|"cross")`; `save()` заповнює `normalized`.

- [ ] Step 1: тести: `derive_family("Passat B7 USA")=="Passat"`, `derive_family("Elantra AD")=="Elantra"`, `derive_family("Grand Vitara")=="Grand Vitara"`, `derive_family("Mercedes W124")` — правило: беремо токени зліва, поки токен не містить цифру і не є `USA|EU|AD|HD|...` (довжина ≤3 і upper); `Generation.label` для (2011, 2014), (2018, None), (None, None); `PartNumber.save` нормалізує.
- [ ] Step 2: FAIL → Step 3: моделі + `translation.py` (`name`, `description` для Category/Product) + адмінка Unfold: `ProductAdmin(ModelAdmin, ImportExportModelAdmin)` з `list_display = (thumb, name, sku, manufacturer, category, price, stock_status, is_active)`, `list_editable=("price","stock_status")`, `search_fields = ("name_uk","sku","part_numbers__normalized")`, `list_filter` (category, manufacturer, stock_status, is_featured), inlines `ProductImageInline`, `PartNumberInline`, `FitmentInline(autocomplete_fields=["generation"])`, actions `make_featured`, `deactivate`. `GenerationAdmin.search_fields=("model__name","model__make__name")`.
- [ ] Step 4: `makemigrations && pytest` — PASS. Step 5: commit.

### Task A4: Контент-моделі (налаштування, банери, акції, сторінки) + ціноутворення

**Files:** Create `backend/apps/content/{models,translation,admin,apps}.py`, `backend/apps/catalog/services/pricing.py`, `backend/tests/test_pricing.py`

**Interfaces — Produces:**
- `SiteSettings.load() -> SiteSettings` (singleton pk=1)
- `Banner(placement, theme, ...)`, `Banner.objects.live(placement)` → активні в межах дат, за `sort`
- `Promotion.objects.live()`; `Promotion.applies_to(product) -> bool`
- `pricing.effective_price(product, promos: list[Promotion] | None = None) -> PriceInfo` де `PriceInfo = dataclass(price: Decimal, sale_price: Decimal|None, old_price: Decimal|None, discount_percent: int|None, promotion_id: int|None)`; правила: ціна 0 → без знижки; найбільша знижка серед застосовних акцій; `sale_price` округлюється до гривні вниз; якщо немає акції, але `old_price > price` → `discount_percent` рахується з `old_price`.
- `pricing.live_promotions() -> list[Promotion]` (кеш на запит).

- [ ] Step 1: тести `test_pricing.py`: без акцій; акція на категорію 15% → 3438 → 2922; дві акції — береться більша; ціна 0 → `sale_price is None`; акція поза датами — ігнорується; `old_price` без акції.
- [ ] Step 2–4: FAIL → реалізація → PASS. Адмінки Unfold: `BannerAdmin` з прев'ю зображення, `PromotionAdmin` з `filter_horizontal`/autocomplete, `PageAdmin` з `WysiwygWidget` Unfold для `body`, `SiteSettingsAdmin` (заборона add/delete).
- [ ] Step 5: commit.

### Task A5: REST API каталогу та контенту

**Files:** Create `backend/apps/catalog/{serializers,views,urls}.py`, `backend/apps/catalog/services/queries.py`, `backend/apps/content/{serializers,views,urls}.py`, `backend/tests/test_api_catalog.py`, `backend/tests/factories.py`

**Interfaces — Produces (JSON contracts, усі шляхи з префіксом `/api`):**
- `ProductCard = {id, slug, name, sku, manufacturer: str|null, image: str|null, price: number, sale_price: number|null, old_price: number|null, discount_percent: int|null, stock_status, generation_ids: int[], category: {slug,name}}`
- `GET /settings` → SiteSettings (phones[], email, address, work_hours, map_embed_url, socials{}, iban_details)
- `GET /home` → `{banners:{hero:[],bento:[],home_strip:[]}, categories: CategoryNode[], featured: ProductCard[12], popular_makes: Make[], promotions: Promotion[]}`
- `GET /categories` → `CategoryNode[] = {id, slug, name, icon, image, product_count, children: CategoryNode[]}`
- `GET /categories/<slug>` → `{..., parent: {slug,name}|null, children}`
- `GET /products/<slug>` → `ProductDetail = ProductCard & {description, side, position, images:[{url,alt}], part_numbers:[{number,kind}], fitments:[{generation_id, make, make_slug, model, model_slug, generation_slug, label, years}], promotion:{slug,title}|null, related: ProductCard[8], breadcrumbs:[{name,href}]}`
- `GET /makes` → `[{id,name,slug,logo,is_popular,product_count}]`
- `GET /makes/<slug>` → `{id,name,slug, families:[{family, models:[{id,name,slug, generations:[{id,slug,label,years_label,year_from,year_to,market,product_count}]}]}]}`
- `GET /generations/<id>` → `CarRef = {generation_id, make, make_slug, model, model_slug, generation_slug, label, full_label, years_label}`
- `GET /cars/<make>/<model>/<gen>` → `CarRef & {categories:[{id,slug,name,count}]}`
- `GET /banners?placement=`, `GET /promotions`, `GET /promotions/<slug>` → `{..., products: ProductCard[]}` (через каталог-запит), `GET /pages`, `GET /pages/<slug>`
- `GET /legacy/resolve?path=/mark/544` → `{"location": "/cars/hyundai"}` або 404
- `queries.product_cards(qs) -> list[dict]` — один prefetch (images, fitments), pricing на пачку.

- [ ] Step 1: factories (прості функції `make_product(**kw)` тощо) + тести: `/home` структура; `/products/<slug>` містить `fitments[0].label` і `sale_price` при акції; `/makes/<slug>` групує моделі за `family`; `/legacy/resolve` для mark і model.
- [ ] Step 2–4: FAIL → реалізація (DRF `APIView`/`ReadOnlyModelViewSet`; `AllowAny`; кеш-заголовки не потрібні — кешує Next) → PASS.
- [ ] Step 5: commit.

### Task A6: Revalidation-сигнали в Next

**Files:** Create `backend/apps/core/revalidate.py`, `backend/apps/catalog/signals.py`, `backend/apps/content/signals.py`, `backend/tests/test_revalidate.py`

**Interfaces — Produces:** `revalidate_tags(tags: list[str]) -> None` (POST `{tags}` на `NEXT_REVALIDATE_URL` з заголовком `x-revalidate-secret`, таймаут 2 с, помилки лише логуються, виклик через `transaction.on_commit`). Теги: `product:<slug>`, `products`, `categories`, `makes`, `home`, `banners`, `promotions`, `pages`, `page:<slug>`, `settings`.

- [ ] Step 1: тест з `monkeypatch` httpx.post: збереження Product → викликано з `["product:<slug>","products","home"]`; помилка мережі не кидає виняток.
- [ ] Step 2–4. Step 5: commit.

## Фаза B — Імпорт даних

### Task B1: Парсери сторінок старого сайту (чисті функції)

**Files:** Create `backend/apps/importer/parsers.py`, `backend/tests/fixtures/premier/{home,product,category,mark}.html` (збережені реальні сторінки), `backend/tests/test_parsers.py`

**Interfaces — Produces:**
```python
@dataclass class CategoryNode: name: str; slug: str|None; icon_url: str|None; children: list["CategoryNode"]
@dataclass class ModelLink: make_legacy_id: int; model_legacy_id: int; series_legacy_id: int; model_name: str; years: tuple[int|None,int|None]
@dataclass class ParsedProduct: url: str; slug: str; name: str; sku: str; manufacturer: str|None; make: str|None; model: str|None; series: str|None; condition: str|None; price: Decimal; in_stock: bool; description: str; image_urls: list[str]; breadcrumbs: list[tuple[str,str]]  # (name, slug)
def parse_home_categories(html) -> list[CategoryNode]
def parse_home_makes(html) -> list[tuple[int, str]]
def parse_mark_models(html, make_legacy_id) -> list[ModelLink]
def parse_category_page(html) -> tuple[list[str], int]   # (product urls, last offset)
def parse_product(html, url) -> ParsedProduct
def parse_years(label: str) -> tuple[int|None, int|None]  # "(2011-2014)"→(2011,2014), "(2018-)"→(2018,None), ""→(None,None)
def parse_side_position(name) -> tuple[side, position]     # «ліва»→left, «права»→right, «передн»→front, «задн»→rear
def parse_page_body(html) -> tuple[str, str]               # (title, cleaned html)
```
- [ ] Step 1: зберегти фікстури (curl реальних сторінок) + тести: на `product.html` — sku `FP7439R1T`, manufacturer `TYC`, model `Passat B7 USA`, series `(2011-2014)`, breadcrumbs `[("Оптика","optika"),("Фари передні","fary-perednie")]`, ≥1 image; на `category.html` — 10 URL і `last offset == 3180`; `parse_home_categories` — «Оптика» має 4 дитини; `parse_mark_models` на `mark.html` (Hyundai) — є `Accent` з years (2011, 2018); `parse_years` кейси.
- [ ] Step 2–4. Step 5: commit.

### Task B2: Кешований HTTP-клієнт і завантажувач у БД

**Files:** Create `backend/apps/importer/{fetch,loader}.py`, `backend/tests/test_loader.py`

**Interfaces — Produces:**
- `Fetcher(cache_dir: Path, concurrency=4, delay=0.25)`: `get(url) -> str` (кеш sha1-файлів, retry 3× backoff), `download(url, dest_dir) -> Path|None`, `map(urls, fn)` (ThreadPool).
- `loader.upsert_category_tree(nodes) -> dict[slug, Category]`
- `loader.upsert_make(legacy_id, name) -> Make`; `loader.upsert_generation(make, ModelLink) -> Generation`
- `loader.upsert_product(p: ParsedProduct, images: list[Path]) -> Product` — ідемпотентно за `legacy_url`; створює Manufacturer, PartNumber (sku як `sku`, номери з назви як `oem`), Fitment (make+model+series → Generation, створює якщо нема), stock `in_stock` якщо JSON-LD InStock, інакше `on_order`; `side/position` з назви; `popularity` = випадкове 0–100 з seed(sku) для демо-сортування.
- [ ] Step 1: тест — двічі `upsert_product` на той самий ParsedProduct → 1 товар, 1 fitment, part_numbers без дублів; нова серія створюється з правильними роками.
- [ ] Step 2–4. Step 5: commit.

### Task B3: Команди `import_premier`, `seed_demo`

**Files:** Create `backend/apps/importer/management/commands/{import_premier,seed_demo}.py`

**Interfaces — Consumes:** B1, B2. **Produces:** CLI `import_premier [--limit 3000] [--per-category 90] [--cache /data/cache] [--skip-images]` і `seed_demo`.

Алгоритм `import_premier`: home → дерево категорій (+іконки) і марки → кожна `/mark/{id}` → моделі/серії → для кожної листової категорії сторінки `/category/<slug>/<offset>` поки не набрано `per_category` URL → дедуп, обрізка до `limit` → паралельно `parse_product` + фото → `upsert_product` → `/page/*` зі sitemap сторінок → підсумок (створено/оновлено/помилок).
`seed_demo`: SiteSettings (контакти з Global Constraints, IBAN-реквізити зі старого сайту), 3 акції («−15% оптика TYC і DEPO», «−10% радіатори», «Кузов за оптовими цінами» 7%), 6 банерів (hero/bento/home_strip/catalog_top, згенеровані з фото товарів + темна тема), синоніми (пасат/passat, камрі/camry, фольксваген/volkswagen/vw, мерседес/mercedes, тойота/toyota, хюндай/хендай/hyundai, кіа/kia, фара/фари/оптика, крило/крила, бампер/бампери), `is_featured` для 16 товарів з фото й ціною, `is_popular` для 16 марок.
- [ ] Step 1: запуск на 30 товарах `--limit 30` — у БД ≥25 товарів із фото, fitment, категорією; повторний запуск — 0 нових.
- [ ] Step 2: повний демо-імпорт `--limit 3000` у фоні (Фаза C/E йдуть паралельно).
- [ ] Step 3: commit.

## Фаза C — Пошук і VIN

### Task C1: Індекс Meilisearch

**Files:** Create `backend/apps/search/{models,documents,index,signals,admin}.py`, `management/commands/reindex_search.py`, `backend/tests/test_documents.py`

**Interfaces — Produces:**
- `product_document(p: Product, price: PriceInfo) -> dict` з полями: `id, slug, name, sku, part_numbers: list[str] (normalized + raw), manufacturer, manufacturer_id, category, category_ids: [leaf, parent], make: list[str], make_ids, model: list[str], model_ids, generation: list[str], generation_ids, side, position, stock_status, price (effective), has_price, promo: bool, popularity, created_at (timestamp), image, card: ProductCard`.
- `index.ensure_settings()`, `index.reindex_all(batch=1000)`, `index.upsert_products(ids)`, `index.delete_products(ids)`, `index.search(q, filters: list[str], facets: list[str], sort, page, hits_per_page) -> dict`, `index.sync_synonyms()`.
- Налаштування: searchable `["name","part_numbers","sku","make","model","generation","category","manufacturer"]`; filterable як у spec; sortable `["price","popularity","created_at"]`; `typoTolerance.disableOnAttributes = ["part_numbers","sku"]`; rankingRules за замовчуванням + `popularity:desc`.
- [ ] Step 1: тест `product_document` (без мережі): `part_numbers` містить і `561941005D`, і `FP7439R1T`; `category_ids` містить батьківську категорію; `price` — ціна зі знижкою.
- [ ] Step 2–4. Сигнали: save/delete Product/Fitment/PartNumber/Promotion → `on_commit` upsert. Step 5: commit.

### Task C2: Розуміння запиту

**Files:** Create `backend/apps/search/{understanding,car_aliases}.py`, `backend/tests/test_understanding.py`

**Interfaces — Produces:**
```python
@dataclass class Understood:
    kind: Literal["vin","part_number","text","empty"]
    raw: str; text: str                     # text = залишок для повнотекстового пошуку
    vin: str|None = None
    part_number: str|None = None            # normalized
    make_id: int|None = None; model_ids: list[int] = field(default_factory=list)
    category_id: int|None = None
def understand(q: str) -> Understood
def translit_variants(latin: str) -> set[str]   # "passat" -> {"пасат","пассат"}; "camry"->{"камрі","камри"}
class CarAliasIndex: build() -> CarAliasIndex; match(tokens) -> (make_id|None, model_ids, consumed_tokens)
```
Правила: VIN → `kind="vin"`; один «номерний» токен (≥5 символів, є цифра, не рік) або рядок, що після нормалізації має ≥6 символів і ≥50% цифр → `part_number`; інакше текст: токени ↔ аліаси марок (name, lower, translit, синоніми) і моделей (name, family, translit; «б7» ↔ «b7» через заміну кирилиці-двійників `а→a, в→b, е→e, к→k, м→m, н→h? ні` — лише для коротких кодів `[а-я]\d+`); категорія: словник основ (`фар→fary-peredni…`, `ліхтар/фонар`, `бампер`, `крил`, `капот`, `дзеркал`, `радіатор`, `скло`, `глушник/вихлоп`, `двер`, `решітк`, `підкрилк/локер`, `поворот`) + назви категорій.
- [ ] Step 1: тести: `understand("1VWBP7A3XCC012345").kind=="vin"`; `understand("5619 41005-D")` → part_number `561941005D`; `understand("фара пасат б7")` → kind text, make=VW, model_ids містять «Passat B7…», category=«Фари передні», `text==""`; `understand("бампер camry 70")` → Toyota Camry; `understand("")` → empty; `translit_variants("passat")` ⊇ {"пасат"}.
- [ ] Step 2–4. Step 5: commit.

### Task C3: API пошуку і лістингів (Meili + fallback Postgres)

**Files:** Create `backend/apps/search/{service,views,urls}.py`, `backend/tests/test_search_api.py`

**Interfaces — Produces:**
- `service.query_products(params: ListingParams) -> ListingResult` де `ListingParams(q, category_slug, make_slug, model_slug, generation_id, car_generation_id, manufacturer_ids, side, stock, price_min, price_max, promo_slug, sort: "popular"|"price_asc"|"price_desc"|"new", page, page_size=24)`; `ListingResult = {count, page, pages, results: ProductCard[], facets: {categories:[{id,slug,name,count}], manufacturers:[{id,name,count}], side:{left,right}, stock:{in_stock,on_order}}, price_range:{min,max}, understood: dict|null, degraded: bool}`.
- `GET /api/products?…` → ListingResult (для категорій, марок, акцій).
- `GET /api/search?q=&…` → ListingResult з `understood` (car → `CarRef`, category → `{slug,name}`).
- `GET /api/search/suggest?q=&car=` → `{kind, vin?, car?: CarRef, category?, products: ProductCard[≤6], categories:[{slug,name,count}] (≤6), total}`; для `part_number` — точні збіги з Postgres першими з прапорцем `exact: true`.
- Fallback: `MeilisearchError`/з'єднання → Postgres (`name__icontains` по токенах + `part_numbers__normalized__startswith`), `degraded=True`.
- [ ] Step 1: тести з `settings.MEILI_URL` на живий meili у compose (маркер `@pytest.mark.meili`) + fallback-тест з вимкненим meili (monkeypatch клієнта, що кидає помилку) — повертає товар за назвою.
- [ ] Step 2–4. Step 5: commit.

### Task C4: VIN-декодер

**Files:** Create `backend/apps/vin/{models,decoder,nhtsa,matching,views,urls,admin}.py`, `fixtures/wmi.json`, `management/commands/load_wmi.py`, `backend/tests/test_vin.py`

**Interfaces — Produces:**
```python
def validate_vin(vin) -> tuple[str, list[str]]      # (clean upper, warnings) ; raises VinError
def check_digit_ok(vin) -> bool
def model_year(vin, today=date.today()) -> int|None
@dataclass class VinInfo: vin; make: str|None; model: str|None; year: int|None; body: str|None; engine: str|None; country: str|None; market: str; source: Literal["nhtsa","wmi"]; warnings: list[str]
def decode(vin) -> VinInfo                          # кеш → NHTSA (4 c) → fallback WMI
def match_generations(info: VinInfo, limit=3) -> list[Generation]
```
- `POST /api/vin/decode {vin}` → `{vin, valid, warnings, make, model, year, body, engine, country, market, source, matches: CarRef[]}` (400 з `{error}` для невалідного).
- `POST /api/vin/requests {vin, name, phone, part_query, comment}` → 201 `{id}`; сповіщення через `orders.notify.notify_manager`.
- [ ] Step 1: тести: `check_digit_ok("1M8GDM9AXKP042788")` True; `model_year("1VWBP7A3XCC012345")==2012`; `model_year` для EU VIN з 10-м символом `B` → 2011; невалідні символи (I,O,Q) → VinError; `decode` з monkeypatch NHTSA (JSON-фікстура Passat 2012 USA) → make Volkswagen, market usa; NHTSA timeout → source wmi; `match_generations` обирає «Passat B7 USA (2011–2014)» замість EU-версії.
- [ ] Step 2–4. Step 5: commit.

## Фаза D — Замовлення

### Task D1: Замовлення, 1 клік, сповіщення, Нова Пошта

**Files:** Create `backend/apps/orders/{models,services,notify,serializers,views,urls,admin,novaposhta}.py`, `backend/tests/test_orders.py`

**Interfaces — Produces:**
- `create_order(data: OrderInput) -> Order` (транзакція; ціни з `pricing.effective_price`; неактивні товари → `ValidationError({"items": ...})`; qty 1–99; номер `PP-{id:06d}`; `access_token = uuid4`).
- `create_quick_order(phone, product_id, name="", qty=1, note="") -> Order`
- `POST /api/orders` → 201 `{number, access_token, total}`; `GET /api/orders/<number>?token=` → підсумок; `POST /api/orders/quick`; `POST /api/cart/validate {items:[{product_id,qty}]}` → `{items:[{product_id, available, card: ProductCard}], total}`.
- `GET /api/np/cities?q=`, `GET /api/np/warehouses?city_ref=&q=` → `{enabled: bool, results: [...]}` (якщо ключа немає — `enabled: false`).
- Телефон: `^\+380\d{9}$` після нормалізації (приймає `063 420 39 93`, `0634203993`).
- [ ] Step 1: тести: total перераховано сервером (клієнтська ціна ігнорується), акція застосовується; неактивний товар → 400; невалідний телефон → 400; quick order створюється з kind quick; notify кидає виняток — замовлення все одно 201; `GET` без токена → 404.
- [ ] Step 2–4. Адмінка: список з кольоровими статусами (Unfold `@display(label=...)`), інлайн позицій read-only, фільтри статус/доставка/дата, сніпет «Авто клієнта». Step 5: commit.

### Task D2: Дашборд адмінки Unfold

**Files:** Create `backend/apps/dashboard/{__init__,views}.py`, `backend/templates/admin/index.html`; Modify `config/settings.py` (`UNFOLD` dict: `SITE_TITLE`, `SITE_HEADER`, `SITE_LOGO`, `COLORS.primary` — золота шкала 50–950, `SIDEBAR.navigation` з групами Каталог/Маркетинг/Контент/Продажі/Пошук, `DASHBOARD_CALLBACK`).
- [ ] Step 1: тест: `GET /admin/` під суперюзером → 200 і містить «Замовлення сьогодні».
- [ ] Step 2–4. Дія «Переіндексувати пошук» (кнопка в SearchSynonym changelist → `reindex_all`). Step 5: commit.

## Фаза E — Фронтенд: основа

### Task E1: Каркас Next.js + Tailwind + next-intl + тема «Платина»

**Files:** Create `frontend/*` (create-next-app 16, TS, Tailwind 4, ESLint, `src/`), `src/i18n/*`, `src/proxy.ts`, `messages/uk.json`, `src/app/[locale]/layout.tsx`, `src/app/globals.css` (токени `@theme`: `--color-graphite`, `--color-platinum-50..300`, `--color-gold-*`, градієнти `.bg-gold`, `.text-gold`, `.bg-platinum`, радіуси, тіні), `frontend/Dockerfile` (multi-stage, `output: "standalone"`), `src/lib/format.ts`, `src/lib/format.test.ts`, `vitest.config.ts`.

**Interfaces — Produces:** `formatPrice(n: number) -> string` («3 438 ₴»; 0 → «Ціну уточнюйте»); `cn(...classes)`; шрифти як CSS-змінні `--font-display` (Unbounded), `--font-sans` (Onest).
- [ ] Step 1: vitest `formatPrice(3438) === "3 438 ₴"`; `formatPrice(0) === "Ціну уточнюйте"`.
- [ ] Step 2–4. `next.config.ts`: `images.localPatterns [{pathname:'/media/**'}]`, `rewrites: /media/:path* → ${BACKEND_INTERNAL_URL}/media/:path*` (для оптимізатора зображень), `output: 'standalone'`. `docker compose up frontend nginx` → `http://localhost:8080` віддає сторінку. Step 5: commit.

### Task E2: API-клієнт, типи, «Моє авто», кошик

**Files:** Create `src/lib/{api,types,vin,car-cookie}.ts`, `src/stores/{cart,my-car}.ts`, `src/lib/vin.test.ts`, `src/stores/cart.test.ts`

**Interfaces — Produces:**
- `types.ts`: TS-типи, що дзеркалять контракти A5/C3/C4/D1 (`ProductCard`, `ProductDetail`, `CategoryNode`, `CarRef`, `ListingResult`, `Suggest`, `VinDecodeResult`, `SiteSettings`, `Banner`, `Promotion`, `Page`, `MakeDetail`).
- `api.ts` (server-only): `apiGet<T>(path, {tags, revalidate=300})` → `fetch(BACKEND_INTERNAL_URL + '/api' + path, {next:{tags, revalidate}})`, 404 → `null`, інші помилки → throw `ApiError`; експорти `getHome()`, `getSettings()`, `getCategories()`, `getCategory(slug)`, `getProduct(slug)`, `getMakes()`, `getMake(slug)`, `getCar(make, model, gen)`, `getGeneration(id)`, `listProducts(params)`, `searchProducts(params)`, `getPromotions()`, `getPromotion(slug)`, `getPage(slug)`, `getPages()`.
- Клієнтський `browserApi` (відносні `/api/...`): `suggest(q, car)`, `decodeVin(vin)`, `createVinRequest`, `createOrder`, `quickOrder`, `validateCart`, `npCities`, `npWarehouses`.
- `vin.ts`: `looksLikeVin(s) -> boolean` (17 символів без I/O/Q після чистки).
- `car-cookie.ts`: `CAR_COOKIE = "pp_car"`, `readCarCookie(): Promise<number|null>` (server, `cookies()`), клієнт `setCarCookie(id|null)`.
- `stores/my-car.ts`: zustand persist `{car: CarRef|null, setCar(car), clear()}` + синхронізація cookie + `router.refresh()`.
- `stores/cart.ts`: zustand persist `{items: {product: ProductCard, qty}[], add(p, qty=1), setQty(id, qty), remove(id), clear(), count(), total()}` (total — з `sale_price ?? price`).
- [ ] Step 1: vitest: `looksLikeVin`; cart add двічі той самий товар → qty 2; `total()` бере `sale_price`.
- [ ] Step 2–4. Step 5: commit.

### Task E3: Бренд, шапка, футер, «Моє авто» пікер, розумний SearchBox

**Files:** Create `src/components/brand/{Logo,Horseshoe}.tsx`, `src/components/layout/{Header,MegaMenu,Footer,MobileNav,CartButton}.tsx`, `src/components/search/{SearchBox,SuggestPanel}.tsx`, `src/components/car/{MyCarChip,MyCarPicker,FitBadge}.tsx`, `src/components/ui/{Button,Dialog,Sheet,Badge,Skeleton,Toast}.tsx`

**Interfaces — Produces:**
- `<Logo variant="full"|"mark" />` — SVG (золота підкова `url(#pp-gold)` + wordmark Unbounded).
- `<SearchBox size="hero"|"header" autoFocus? />` — ARIA combobox; debounce 120 мс; `browserApi.suggest`; стани: VIN (темна картка авто + «Показати N деталей» + «Зробити моїм авто» + «Запит за VIN»), номер (точний збіг з бейджем, аналоги), текст («Ми зрозуміли: …» чипи, товари, категорії); Enter → `/search?q=`; Esc закриває; ↑↓ навігація; Motion-анімація панелі.
- `<MyCarPicker open onOpenChange />` — вкладки «VIN» / «Марка і модель»; кроки Марка (популярні зверху + пошук) → Модель (групи за family) → Роки (генерації); `setCar`.
- `<MyCarChip />` — у шапці; порожній стан «Вкажіть авто».
- `<FitBadge generationIds={number[]} />` — «Підходить» / «Може не підходити» / нічого.
- [ ] Step 1: Playwright-сценарій пізніше (G1); тут — `npm run lint && npm run typecheck && vitest`.
- [ ] Step 2: візуальна перевірка в браузері: шапка, пошук з підказками на реальних даних, вибір авто.
- [ ] Step 3: commit.

## Фаза F — Фронтенд: сторінки

### Task F1: Головна

**Files:** Create `src/app/[locale]/page.tsx`, `src/components/home/{Hero,HeroLines,Bento,PopularMakes,Featured,Benefits,PromoStrip,AboutBlock}.tsx`, `src/components/product/ProductCard.tsx`, `src/components/catalog/BannerSlot.tsx`

Зміст — з spec §5: герой (заголовок «Знайдіть точну деталь для свого авто», пігулка «N деталей», великий SearchBox, підказки-чипи; anime.js: промальовування золотих ліній + лічильник), бенто (головна акція з банера `bento` + 4 категорії з лічильниками), «Моє авто» CTA-смуга, популярні марки, хіти (`featured`), банер `home_strip`, переваги, блок про компанію, JSON-LD `AutoPartsStore`. `ProductCard` — фото 4:3, бейдж наявності/знижки, FitBadge, назва (2 рядки), артикул · виробник, ціна (стара закреслена), кнопка «У кошик» (анімація «польоту»); ціна 0 → «Запитати ціну» (QuickOrderDialog).
- [ ] Step 1: typecheck/lint. Step 2: візуальна перевірка десктоп 1440 і мобільний 390. Step 3: commit.

### Task F2: Каталог, категорія, пошук, акції (лістинги з фільтрами)

**Files:** Create `src/app/[locale]/catalog/page.tsx`, `category/[slug]/page.tsx`, `search/page.tsx`, `promotions/page.tsx`, `promotions/[slug]/page.tsx`; `src/components/catalog/{Listing,Filters,FiltersSheet,SortSelect,Pagination,ActiveCarBanner,CategoryGrid,Breadcrumbs}.tsx`

**Interfaces — Consumes:** `listProducts`, `searchProducts`, `readCarCookie`. Фільтри — через URL searchParams (серверний рендер), клієнтський `Filters` оновлює URL (`router.replace`, `useTransition`). «Моє авто» → `car_generation_id` у запиті + `ActiveCarBanner` («Показуємо лише деталі, що підходять для … · Показати всі» → `?all_cars=1`).
- [ ] Step 1: typecheck/lint. Step 2: візуальна перевірка фільтрів, сортування, пагінації, мобільного sheet. Step 3: commit.

### Task F3: Навігація за авто

**Files:** Create `src/app/[locale]/cars/page.tsx`, `cars/[make]/page.tsx`, `cars/[make]/[model]/page.tsx`, `cars/[make]/[model]/[generation]/page.tsx`; `src/components/car/{MakeGrid,ModelList,GenerationCard,SetMyCarButton}.tsx`
- Серія: заголовок «Запчастини для Volkswagen Passat B7 USA (2011–2014)», кнопка «Зробити моїм авто», категорії з лічильниками, лістинг.
- [ ] Step 1–3: typecheck/lint, перевірка, commit.

### Task F4: Сторінка товару

**Files:** Create `src/app/[locale]/product/[slug]/page.tsx`, `src/components/product/{Gallery,BuyBox,PartNumbers,FitmentTable,DeliveryInfo,RelatedProducts,QuickOrderDialog}.tsx`
- `generateMetadata` (title «{name} — купити в Києві | Premier Parts», description, OG-зображення), JSON-LD Product + BreadcrumbList. Галерея з зумом (Motion `layoutId`), копіювання номерів, FitBadge великий, таблиця сумісності з посиланнями на серії, «У кошик», «Купити в 1 клік», доставка/оплата з SiteSettings, схожі.
- [ ] Step 1–3.

### Task F5: Кошик, оформлення, успіх, VIN-сторінка

**Files:** Create `src/app/[locale]/cart/page.tsx`, `checkout/page.tsx`, `checkout/success/[number]/page.tsx`, `vin/page.tsx`; `src/components/cart/{CartView,CartLine}.tsx`, `src/components/checkout/{CheckoutForm,DeliveryFields,NpAutocomplete,OrderSummary}.tsx`, `src/components/vin/{VinDecoder,VinRequestForm}.tsx`; `src/lib/schemas.ts` (zod: phone, order, vin request)
- Кошик: `validateCart` при відкритті (оновлює ціни/наявність, повідомляє про зміни). Оформлення: react-формa на zod, маска телефону, радіо-картки доставки/оплати, NP-автопідказка якщо `enabled`, підсумок праворуч, submit → `createOrder` → `router.push(/checkout/success/PP-…?token=…)` + `cart.clear()`. Успіх: номер, склад, реквізити для оплати (якщо `iban`), кроки «що далі». VIN: декодер з результатом і «Зробити моїм авто», форма запиту.
- [ ] Step 1–3.

### Task F6: Статичні сторінки, контакти, SEO-файли, редиректи, 404/500

**Files:** Create `src/app/[locale]/page/[slug]/page.tsx`, `contacts/page.tsx`, `not-found.tsx`, `error.tsx`, `src/app/sitemap.ts`, `src/app/robots.ts`, `src/app/api/revalidate/route.ts`, `src/lib/seo.ts`; Modify `src/proxy.ts` (`/mark/*`, `/model/*` → `GET /api/legacy/resolve` → 301).
- `route.ts`: перевіряє `x-revalidate-secret`, `revalidateTag(tag, "max")` для кожного тега (перевірити сигнатуру Next 16).
- [ ] Step 1: тест curl: `POST /api/revalidate` без секрету → 401; `/mark/544` → 301 на `/cars/hyundai`. Step 2–3.

## Фаза G — Перевірка

### Task G1: E2E smoke і полірування

**Files:** Create `frontend/playwright.config.ts`, `frontend/e2e/smoke.spec.ts`
- Сценарій: головна → ввести «фара» → підказки видно → Enter → результати → відкрити товар з ціною → «У кошик» → кошик → оформлення (Самовивіз, Карткою) → успіх з номером `PP-`. Другий: VIN «1VWBP7A3XCC012345» у пошуку → «Зробити моїм авто» → чип у шапці.
- Lighthouse (mobile) на головній/лістингу/товарі; виправити все < 90.
- Перевірка адмінки: створити банер → з'являється на головній без перезапуску (revalidation).
- README з інструкцією запуску й демо-сценарієм для клієнта.
- [ ] Step 1–3: запуск, виправлення, commit.
