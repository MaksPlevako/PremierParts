# Premier Parts V1 — дизайн і специфікація

Дата: 2026-09-21 · Статус: затверджено (напрямок, пошук, архітектура; решта — рішення команди розробки)

## 1. Мета

Преміальна («люкс») версія інтернет-магазину кузовних запчастин premier-parts.com.ua для демонстрації клієнту й отримання апруву.

Головна вимога клієнта: **сайт простий і легкий у використанні, пошук зрозумілий**.
Конкуренти, яких треба перевершити: carera.com.ua, kyivparts.com, autox.pro (CMS: cms.autox.pro). У жодного з них немає зручного пошуку за VIN, у всіх слабкі фільтри.

### Входить у V1
- Каталог (категорії, марки → моделі → серії, виробники), картка товару, акції, банери та реклама, статичні сторінки.
- Розумний пошук одним полем: VIN / номер деталі / текст із помилками й транслітерацією.
- «Моє авто»: вибране авто фільтрує весь сайт; зберігається без реєстрації.
- Кошик, оформлення замовлення, «Купити в 1 клік», запит за VIN. Усе потрапляє в адмінку.
- Адмінка Django (Unfold): редагування всіх даних, банерів, акцій, синонімів пошуку, замовлень.
- Імпортер старого сайту (для демо ~3 000 товарів; повний каталог — 37 452).
- Лише українська мова, але архітектура готова до інших мов.

### Не входить у V1
Реєстрація та профіль, реальна онлайн-оплата, продакшн-деплой (лише локальний Docker Compose), платні VIN-каталоги (Laximo/TecDoc), інтеграція з 1С/складом.

## 2. Візуальний напрямок — «Платина» (варіант C)

- Фон: сріблясто-сірі металеві градієнти (`#EEF0F2 → #F7F8F9 → #FFFFFF`), конічні «блискучі» плями в героях.
- Текст і темні елементи: графіт `#15181C`.
- Золото — лише акцент: градієнт `#9C7424 → #E7C573 → #F7E6B0 → #B98E3A` (кнопки CTA, підсвічування, «Моє авто», значки). Золото ніколи не використовується для тексту основного контенту (контраст AA).
- Темні блоки акцій: `#15181C → #2A2E35 → #6D5522`.
- Шрифти: **Unbounded** (заголовки, ціни) + **Onest** (текст); обидва з кирилицею, через `next/font`.
- Радіуси 12–22 px, м'які тіні, «скляна» шапка (blur).
- Логотип: векторна інтерпретація оригіналу (золота підкова + словесний знак PREMIER PARTS). Оригінальний JPG зберігається як референс.
- Анімації: Motion для UI (меню, модалки, layout-переходи, «політ» у кошик), anime.js для героя (промальовування золотих ліній і підкови, лічильники). Повага до `prefers-reduced-motion`.

## 3. Архітектура

```
PremierParts/
├─ docker-compose.yml        # postgres, meilisearch, backend, frontend, nginx
├─ .env.example
├─ nginx/default.conf        # http://localhost:8080 — єдина точка входу
├─ frontend/                 # Next.js 16 (App Router, TS strict, Tailwind v4, Motion, anime.js, next-intl, zustand)
└─ backend/                  # Django 5.2 LTS + DRF + django-unfold + modeltranslation + Meilisearch
   ├─ config/
   └─ apps/{core,catalog,search,vin,orders,content,importer}
```

- Nginx: `/` → Next.js, `/api/`, `/admin/`, `/media/`, `/static/` → Django. Один origin, без CORS.
- Next.js-сторінки — серверні компоненти. Вони читають Django API через внутрішню мережу (`http://backend:8000`) з `fetch(..., { next: { tags } })`.
- On-demand revalidation: сигнал `post_save`/`post_delete` у Django викликає `POST /api/revalidate` у Next (секрет у `.env`) з тегами (`product:<id>`, `catalog`, `banners`, `settings`…).
- Браузер звертається до `/api/search/suggest` (Django). Django класифікує запит і звертається до Meilisearch.
- Postgres — джерело правди; Meilisearch — похідний індекс (повний reindex командою + інкрементальні оновлення сигналами).
- i18n: next-intl, маршрути `app/[locale]/…`, `uk` за замовчуванням без префікса (`localePrefix: 'as-needed'`). Бекенд: django-modeltranslation для назв, описів і текстів контенту; API приймає `?lang=` / `Accept-Language`.

## 4. Модель даних (Django)

### catalog
- `Make`: name, slug, logo, is_popular, sort, legacy_id.
- `CarModel`: make FK, name, slug, legacy_id. Унікальність (make, slug).
- `Generation`: model FK, name (напр. «Passat B7 USA»), year_from, year_to (null = досі), market (`eu|usa|asia|other`), slug, legacy_id. Людська назва: `"{model} ({years})"`.
- `Category`: parent FK (null), name*, slug (legacy slug зберігається), icon (ключ SVG-іконки), image, sort, description*.
- `Manufacturer`: name, slug, logo, country.
- `Product`: name*, slug (legacy slug), sku, manufacturer FK, category FK, description*, price (Decimal, 0 = «ціну уточнюйте»), old_price, stock_status (`in_stock|on_order|out_of_stock`), side (`left|right|both|none`), position (`front|rear|none`), condition (`new`), is_active, is_featured, popularity (int), legacy_url, created_at, updated_at.
- `ProductImage`: product FK, image, alt, sort.
- `Fitment`: product FK, generation FK (унікальна пара).
- `PartNumber`: product FK, number (як є), normalized (A–Z0–9, верхній регістр, індекс), kind (`sku|oem|cross`).

(* — перекладні поля через modeltranslation)

### content
- `SiteSettings` (singleton): phones (JSON: номер, мітка, viber), email, address*, work_hours*, map_embed_url, socials, iban_details*, seo_title*, seo_description*.
- `Banner`: title*, subtitle*, image, image_mobile, link, cta_label*, placement (`hero|bento|catalog_top|product_side|home_strip`), theme (`dark|light|gold`), starts_at, ends_at, sort, is_active.
- `Promotion`: title*, slug, description*, discount_percent, image, starts_at, ends_at, categories M2M, manufacturers M2M, products M2M, is_active. Діюча акція з найбільшою знижкою автоматично визначає `sale_price` товару (сервіс `pricing.effective_price`).
- `Page`: title*, slug (legacy slug), body* (HTML/WYSIWYG), seo_title*, seo_description*, show_in_footer, sort.

### search
- `SearchSynonym`: term, synonyms (список). Синхронізується в налаштування Meilisearch.

### vin
- `Wmi`: code (3 символи), make_name, country. Фікстура (~250 кодів).
- `VinDecodeCache`: vin (unique), payload JSON, created_at.
- `VinRequest`: vin, name, phone, part_query, comment, decoded (JSON), status (`new|in_progress|done`), created_at.

### orders
- `Order`: number (`PP-000123`), kind (`regular|quick`), status (`new|confirmed|shipped|completed|canceled`), customer_name, phone, email, delivery_method (`np_branch|np_courier|pickup|taxi`), city, np_branch, address, payment_method (`iban|card_pickup|cash_pickup`), comment, car_snapshot (JSON з «Мого авто»), subtotal, discount, total, user (FK null — для V2), created_at.
- `OrderItem`: order FK, product FK (null on delete), name, sku, price, qty, line_total.

### Збереження SEO-адрес
- `/product/<legacy-slug>` і `/category/<legacy-slug>` лишаються як є.
- `/page/<slug>` лишається.
- `/mark/<legacy_id>` → 301 на `/cars/<make-slug>`; `/model/<mark>/<model>/<series>` → 301 на `/cars/<make>/<model>/<generation>`. Резолвер у Django `GET /api/legacy/resolve?path=…`, редирект у Next middleware / route handler.

## 5. Сторінки фронтенду

| Маршрут | Зміст |
|---|---|
| `/` | Герой із розумним пошуком (anime.js), бенто: головна акція + 4 категорії, смуга «Моє авто»/вибір авто, популярні марки, хіти продажу, банер-реклама, переваги (50+ марок, НП 1–2 дні, 14 днів повернення, самовивіз у Києві), блок про компанію, футер |
| `/catalog` | Усі категорії деревом з іконками й лічильниками |
| `/category/[slug]` | Лістинг: фільтри (підкатегорія, марка/модель/серія, виробник, сторона, наявність, ціна), сортування, пагінація, «Показати ще» |
| `/cars` | Усі марки (логотипи/назви, популярні зверху) |
| `/cars/[make]`, `/cars/[make]/[model]`, `/cars/[make]/[model]/[generation]` | Навігація за авто; на рівні серії — «Зробити моїм авто» + категорії з лічильниками + товари |
| `/product/[slug]` | Галерея із зумом, назва, артикул/OEM (копіювання), ціна/акція, наявність, «Підходить для вашого авто» / «Не підходить», таблиця сумісності, у кошик, 1 клік, доставка й оплата, схожі товари, JSON-LD Product + BreadcrumbList |
| `/search?q=` | Результати з розумінням запиту, фасети, ті самі картки |
| `/promotions`, `/promotions/[slug]` | Акції та товари акції |
| `/vin` | Декодер VIN + форма запиту менеджеру |
| `/cart`, `/checkout`, `/checkout/success/[number]` | Кошик, оформлення, підтвердження |
| `/page/[slug]`, `/contacts` | Статичні сторінки, контакти з картою |
| `not-found`, `error` | Брендовані 404/500 |

Метадані: `generateMetadata` на кожній сторінці, canonical, Open Graph, `sitemap.ts` (з пагінацією через `generateSitemaps`), `robots.ts`, JSON-LD `AutoPartsStore` на головній.

### Ключові компоненти
`Header` (скляна шапка, мега-меню каталогу, SearchBox, MyCarChip, CartButton), `SearchBox` (ARIA combobox, debounce 120 мс, клавіатурна навігація), `MyCarPicker` (модалка: VIN або марка → модель → серія, з пошуком), `ProductCard`, `Filters` (сайдбар на десктопі / bottom sheet на мобільному), `BannerSlot`, `Bento`, `Breadcrumbs`, `Price`, `StockBadge`, `FitBadge`, `QuickOrderDialog`, `Footer`.

### Стан на клієнті
- Кошик: zustand + localStorage.
- «Моє авто»: zustand + **cookie `pp_car`** (id серії), щоб серверні компоненти рендерили фільтровані лістинги й значки «Підходить» уже в HTML.

## 6. Розумний пошук

### Класифікація запиту (Django, `search/understanding.py`)
1. Нормалізація (trim, уніфікація лапок і дефісів).
2. **VIN**: `^[A-HJ-NPR-Z0-9]{17}$` (після видалення пробілів) → VIN-флоу.
3. **Номер деталі**: один токен (або токен із пробілами/дефісами), ≥ 5 символів, містить цифри → `normalize()` і точний пошук у `PartNumber.normalized`. Якщо не знайдено, пошук префіксом, потім Meilisearch без typo-tolerance по номерах.
4. **Текст**: розпізнавання авто (словник аліасів марок і моделей, латиниця + автоматична кирилична транслітерація + синоніми з адмінки; «б7» → «B7») і категорії (ключові слова: назви категорій, форми слів «фара/фари», синоніми). Решта токенів іде в Meilisearch з фільтрами. Якщо результатів 0, фільтри послаблюються.

### Індекс Meilisearch `products`
- searchable (у порядку ваги): `name`, `part_numbers`, `sku`, `make`, `model`, `generation`, `category`, `manufacturer`.
- filterable: `category_ids`, `manufacturer_id`, `make_ids`, `model_ids`, `generation_ids`, `side`, `stock_status`, `price`, `has_price`, `promo`.
- sortable: `price`, `popularity`, `created_at`.
- typo tolerance вимкнена на `part_numbers` і `sku`.
- синоніми: `SearchSynonym` + автоматично згенеровані транслітерації марок і моделей.

### API
- `GET /api/search/suggest?q=&car=` → `{ kind: vin|part_number|text, vin?, car?, category?, products[≤6], categories[{id,name,count}], total }`
- `GET /api/search?q=&filters…&page=` → повні результати + фасети.

### VIN-декодер (`vin/decoder.py`)
- Валідація: довжина, символи; контрольна цифра (9-та) — лише попередження (обов'язкова тільки для Північної Америки).
- WMI (1–3) → марка й країна (фікстура).
- Рік (10-й символ) із циклом 30 років: для північноамериканських VIN 7-ма позиція-літера → 2010+, інакше найближчий рік ≤ поточного.
- NHTSA vPIC `DecodeVinValues/{vin}?format=json` (таймаут 4 с, кеш у `VinDecodeCache`) → Make, Model, ModelYear, BodyClass, DisplacementL, PlantCountry.
- Зіставлення з каталогом: Make за назвою/аліасом → CarModel за збігом назви (Passat → «Passat B7», «Passat B7 USA»…) → Generation, що містить рік; для VIN зі США перевага market=usa. Кілька кандидатів → користувач обирає з 2–3 варіантів.
- Помилки мережі → результат лише з WMI + рік + форма запиту менеджеру.

### «Моє авто»
- Встановлюється з VIN, з вибору в модалці або кнопкою на сторінці серії.
- Чип у шапці (золотий), хрестик скидає.
- Лістинги, пошук і акції фільтруються за `generation_ids`; банер «Показуємо лише деталі, що підходять…» з посиланням «Показати всі».
- Картка товару: «Підходить для {авто}» або м'яке попередження «Може не підходити».

## 7. Замовлення

- Кошик → `/checkout`: ім'я, телефон (маска +380), email (необов'язково), доставка (Нова Пошта відділення / НП кур'єр / самовивіз: Київ, вул. Вікентія Беретті 6Б, завдаток 300 грн / таксі по Києву), місто та відділення, оплата (на рахунок ФОП / карткою чи готівкою при самовивозі), коментар.
- Нова Пошта: автопідказка міст і відділень через API НП, якщо задано `NOVA_POSHTA_API_KEY`; інакше звичайні текстові поля.
- `POST /api/orders` — сервер повторно рахує ціни (з акціями), перевіряє активність товарів, створює `Order` у транзакції та повертає номер.
- «Купити в 1 клік» — `POST /api/orders/quick` (телефон + товар).
- Сповіщення менеджеру: email (у V1 — console backend) + Telegram, якщо задано `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`. Помилка сповіщення не блокує замовлення.
- Товари з ціною 0: «Ціну уточнюйте» + кнопка «Запитати ціну» (quick order із позначкою).

## 8. Адмінка (Unfold)

- Брендування: логотип, золотий акцент, українська локаль.
- Дашборд: замовлення сьогодні/тиждень, нові VIN-запити, товарів активних / без ціни / без фото, останні замовлення.
- Навігація: Каталог (Товари, Категорії, Марки, Моделі, Серії, Виробники), Маркетинг (Банери, Акції), Контент (Сторінки, Налаштування сайту), Продажі (Замовлення, VIN-запити), Пошук (Синоніми, «Переіндексувати»).
- Товар: мініатюра в списку, фільтри, пошук по артикулу/OEM, інлайни фото / номерів / сумісності (autocomplete), дії «Зробити хітом», «Зняти з продажу».
- Імпорт/експорт CSV цін і наявності (django-import-export з інтеграцією Unfold).

## 9. Імпортер (`manage.py import_premier`)

- Джерело: sitemap-и (`/map/mapproduct{0..7}.xml`, `/map/mapurl_category.xml`, `/map/mapurl_page.xml`), сторінки `/mark/{id}` (моделі й серії), сторінки категорій, сторінки товарів.
- Товар: JSON-LD (name, sku, brand, image, price, availability) + таблиця «Характеристики» (Артикул, Виробник, Марка, Модель, Серія, Стан) + опис + усі фото галереї. OEM-номери: з дужок у назві та токенів slug. Сторона/позиція: з назви («ліва/права», «передня/задня»).
- Демо-вибірка: рівномірно по категоріях (`--per-category N`) + загальний ліміт `--limit 3000`.
- Ввічливий краулінг: 4 паралельні запити, retry з backoff, User-Agent проєкту, кеш HTML на диску (повторний запуск не ходить у мережу), upsert за `legacy_url` (ідемпотентно), фото з перевіркою хешу.
- Окремі команди: `seed_demo` (налаштування сайту, акції, банери, синоніми, хіти), `load_wmi`, `reindex_search`.

## 10. Обробка помилок

- Django API недоступний → сторінки показують брендований стан «Тимчасово недоступно»; головна рендерить закешований ISR-варіант.
- Meilisearch недоступний → fallback на Postgres (`icontains` за назвою + точний пошук по номерах), у відповіді прапорець `degraded`.
- NHTSA недоступний → декодування лише за WMI + форма запиту.
- Валідація форм: помилки з DRF відображаються біля полів; на клієнті — ті самі правила (zod).
- Логування: структуровані логи Django; помилки сповіщень пишемо в лог, замовлення не падає.

## 11. Якість і тести

- Backend (pytest-django): нормалізація номерів, класифікація запиту, VIN (рік, WMI, контрольна цифра, зіставлення з каталогом), ціноутворення з акціями, створення замовлення (перерахунок цін, транзакція), парсери імпортера на збережених HTML-фікстурах, API-контракти ключових ендпоінтів.
- Frontend: TypeScript strict + ESLint; Vitest для утиліт (форматування цін, VIN-regex, cookie «Мого авто»); Playwright smoke: пошук → товар → кошик → оформлення → успіх.
- Продуктивність: `next/image` (AVIF/WebP, розміри), ISR, мінімум клієнтського JS (клієнтські лише інтерактивні острівці). Ціль Lighthouse ≥ 90 (mobile) на головній, лістингу й товарі.
- Доступність: контраст AA, focus-стилі, ARIA для combobox і модалок, клавіатурна навігація.

## 12. Запуск

```
cp .env.example .env
docker compose up -d --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py load_wmi
docker compose exec backend python manage.py import_premier --limit 3000
docker compose exec backend python manage.py seed_demo
docker compose exec backend python manage.py reindex_search
# сайт: http://localhost:8080   адмінка: http://localhost:8080/admin
```
