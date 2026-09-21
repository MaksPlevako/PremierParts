# Premier Parts — V1 (демо для клієнта)

Преміальна версія інтернет-магазину кузовних запчастин [premier-parts.com.ua](https://premier-parts.com.ua): розумний пошук (VIN / номер деталі / текст), «Моє авто», каталог з фільтрами, акції й банери, кошик і оформлення замовлення, адмінка для керування всім вмістом.

- Специфікація: [docs/superpowers/specs/2026-09-21-premier-parts-v1-design.md](docs/superpowers/specs/2026-09-21-premier-parts-v1-design.md)
- План реалізації: [docs/superpowers/plans/2026-09-21-premier-parts-v1.md](docs/superpowers/plans/2026-09-21-premier-parts-v1.md)

## Стек

| Шар | Технології |
|---|---|
| Фронтенд | Next.js 16 (App Router, серверні компоненти, `generateMetadata`, ISR за тегами), React 19, TypeScript, Tailwind CSS 4, Motion, anime.js, next-intl, zustand |
| Бекенд | Django 5.2 LTS, Django REST Framework, django-unfold (адмінка), django-modeltranslation, django-import-export |
| Дані | PostgreSQL 17, Meilisearch 1.54 (пошук, фасети, синоніми) |
| Інфраструктура | Docker Compose, Nginx (єдина точка входу `:8080`) |

## Запуск

```bash
cp .env.example .env
docker compose up -d --build

# перший запуск: дані
docker compose exec backend python manage.py load_wmi                      # коди виробників для VIN
docker compose exec backend python manage.py import_premier --limit 3000   # імпорт зі старого сайту (~45 хв, кешується)
docker compose exec backend python manage.py seed_demo                     # акції, банери, синоніми, хіти + переіндексація
docker compose exec backend python manage.py createsuperuser
```

- Сайт: <http://localhost:8080>
- Адмінка: <http://localhost:8080/admin/> (у поточній локальній базі створено `admin` / `PremierDemo2026`; для будь-якого іншого середовища створіть власного користувача)
- API: <http://localhost:8080/api/health>

Повний каталог (37 452 товари): `import_premier --limit 40000 --per-category 5000`. Повторний запуск не дублює товари: HTML і фото кешуються в томі `importcache`.

### Розробка без Docker для фронтенду

```bash
cd frontend
printf 'BACKEND_INTERNAL_URL=http://localhost:8000\nNEXT_PUBLIC_SITE_URL=http://localhost:3000\n' > .env.local
npm install && npm run dev        # http://localhost:3000 (API і /media проксіюються в Django на :8000)
```

## Тести

```bash
docker compose exec backend pytest            # 119 тестів: пошук, VIN, ціни й акції, замовлення, імпорт, API, адмінка
cd frontend && npx vitest run                 # юніт-тести (ціни, VIN, кошик, «Моє авто»)
cd frontend && npx playwright test            # e2e на десктопі й мобільному: пошук → товар → кошик → замовлення, VIN → «Моє авто», фільтри, 301
```

## Сценарій демо для клієнта (5 хвилин)

1. **Головна.** Одне поле пошуку. Ввести `фара пасат B7`: система сама розпізнає категорію («Фари передні») і авто («Volkswagen Passat B7»), а підказки з'являються під час введення.
2. **VIN.** Ввести `1VWBP7A3XCC012345`: розшифровка (Passat 2012, США), кнопка «Показати деталі» відкриває підбір для Passat B7 USA, і авто стає «Моїм авто».
3. **«Моє авто».** Золотий чип у шапці. Каталог, пошук і акції показують лише сумісні деталі, на картках видно позначку «Підходить». Працює без реєстрації.
4. **Номер деталі.** Ввести OEM, наприклад `2GM823031D` або `5619 41005-D` (пробіли й дефіси не заважають): точний збіг і аналоги.
5. **Каталог.** Фільтри за виробником, стороною, наявністю, ціною; сортування. Усе зберігається в URL, тож посиланням можна поділитися.
6. **Товар.** Галерея із зумом, номери з кнопкою копіювання, сумісність, акційна ціна, «Купити в 1 клік».
7. **Оформлення.** Нова Пошта / самовивіз / таксі, оплата. Після підтвердження замовлення одразу з'являється в адмінці разом з авто клієнта.
8. **Адмінка.** Дашборд, замовлення, запити за VIN, товари з мініатюрами (ціни редагуються прямо в списку, імпорт/експорт CSV/XLSX), банери, акції, синоніми пошуку. Зміни видно на сайті одразу.

## Що всередині

```
backend/apps/
  catalog/    марки → моделі → серії, категорії, товари, фото, OEM-номери, сумісність; ціни з урахуванням акцій
  content/    налаштування сайту, банери та реклама, акції, статичні сторінки
  search/     індекс Meilisearch, розуміння запиту (VIN / номер / текст + авто + категорія), фасети, запасний пошук у Postgres
  vin/        декодер VIN (контрольна цифра, рік, WMI, NHTSA vPIC), зіставлення з каталогом, запити менеджеру
  orders/     замовлення з перерахунком цін на сервері, «в 1 клік», Нова Пошта, сповіщення (email / Telegram)
  importer/   парсер старого сайту, ідемпотентний імпорт, seed_demo
  dashboard/  дашборд адмінки
frontend/src/
  app/[locale]/   сторінки (uk без префікса; нова мова = locale у routing.ts + messages/<locale>.json)
  components/     search, car («Моє авто»), catalog, product, cart, checkout, vin, home, layout
```

Старі URL збережені: `/product/<slug>`, `/category/<slug>` і `/page/<slug>` працюють як раніше, а `/mark/<id>` та `/model/...` віддають 301 на нові сторінки марок і моделей.

## Інтеграції (необов'язково, через `.env`)

- `NOVA_POSHTA_API_KEY` — автопідказка міст і відділень у формі замовлення (без ключа — звичайні поля).
- `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` — сповіщення менеджеру про замовлення й запити за VIN (email у V1 виводиться в лог).

## Відомі обмеження V1

- Каталог для демо: 2 681 товар (з 37 452); повний імпорт — однією командою.
- VIN розшифровується безкоштовно (NHTSA + WMI): визначаються марка, модель і рік, але не конкретні OEM-деталі. Для підбору деталей за VIN знадобиться платний каталог (Laximo / TecDoc), архітектура це передбачає.
- Реєстрації, профілю й онлайн-оплати немає (за домовленістю). Поле `Order.user` уже є для V2.
- Lighthouse (mobile, емуляція повільного 4G): Accessibility 96, Best Practices 100, SEO 100, Performance ≈ 73. Реальний перший кадр на прогрітому сервері ≈ 0,3 с. Резерв: менше клієнтського JS у шапці й героях.
