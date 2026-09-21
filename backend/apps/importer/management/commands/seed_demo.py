"""Demo content on top of imported data: settings, promotions, banners, synonyms, featured products."""

from datetime import timedelta
from urllib.parse import quote

from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.utils import timezone

from apps.catalog.models import Category, Make, Product, StockStatus
from apps.content.models import Banner, Promotion, SiteSettings
from apps.core.revalidate import revalidate_tags, suppress_revalidation
from apps.search.models import SearchSynonym

ADDRESS = "Київ, вул. Вікентія Беретті, 6Б"

SYNONYMS = {
    # makes
    "volkswagen": "фольксваген, фольцваген, vw, вв",
    "mercedes-benz": "мерседес, мерс, mercedes, бенц",
    "toyota": "тойота",
    "hyundai": "хюндай, хендай, хундай, хьюндай, хюндаі",
    "kia": "кіа, кия",
    "skoda": "шкода",
    "renault": "рено",
    "peugeot": "пежо",
    "citroen": "сітроен, ситроен",
    "nissan": "ніссан, нісан, ниссан",
    "mitsubishi": "мітсубісі, міцубісі, мицубиси",
    "mazda": "мазда",
    "honda": "хонда",
    "bmw": "бмв, бемве",
    "audi": "ауді, ауди",
    "opel": "опель",
    "ford": "форд",
    "chevrolet": "шевроле, шеви",
    "lexus": "лексус",
    "subaru": "субару",
    "volvo": "вольво",
    "fiat": "фіат, фиат",
    "daewoo": "деу, дэу, дево",
    "chery": "чері, чери",
    "geely": "джилі, джили",
    "porsche": "порше",
    "tesla": "тесла",
    "jeep": "джип",
    "suzuki": "сузукі, сузуки",
    "dacia": "дачія, дача",
    "ssangyong": "санйонг, ссангйонг, санг йонг",
    # models
    "camry": "камрі, камри",
    "passat": "пасат, пассат",
    "golf": "гольф",
    "octavia": "октавія, октавия",
    "corolla": "королла, корола",
    "rav4": "рав4, рав 4, rav 4",
    "focus": "фокус",
    "sportage": "спортейдж, спортаж",
    "tucson": "туксон, тусан",
    "elantra": "елантра, элантра",
    "sonata": "соната",
    "qashqai": "кашкай",
    "logan": "логан",
    "duster": "дастер, дустер",
    "megane": "меган, мегане",
    "lanos": "ланос",
    "jetta": "джета, джетта",
    "tiguan": "тігуан, тигуан",
    "touareg": "туарег",
    "transporter": "транспортер",
    "sprinter": "спрінтер, спринтер",
    "vito": "віто, вито",
    # parts
    "фара": "фари, оптика, headlight",
    "ліхтар": "фонарь, фонар, стоп",
    "бампер": "бампери",
    "крило": "крила, крыло",
    "дзеркало": "зеркало, дзеркала",
    "радіатор": "радиатор, радіатори",
    "скло": "стекло",
    "двері": "дверь, дверка, двер",
    "решітка": "решетка, решітки, грати",
    "підкрилок": "локер, подкрылок, підкрилки",
    "глушник": "глушитель, вихлоп",
}


class Command(BaseCommand):
    help = "Seed demo content (promotions, banners, synonyms, featured products, site settings)"

    def handle(self, *args, **opts):
        with suppress_revalidation():
            self.site_settings()
            self.popular_makes()
            featured = self.featured()
            promos = self.promotions()
            self.banners(promos, featured)
            self.synonyms()
        try:
            from apps.search.index import reindex_all

            self.stdout.write(f"Проіндексовано: {reindex_all()}")
        except Exception as exc:
            self.stderr.write(f"Пошук не переіндексовано: {exc}")
        revalidate_tags(["home", "banners", "promotions", "products", "settings", "makes"], immediate=True)
        self.stdout.write(self.style.SUCCESS("Демо-дані готові"))

    def site_settings(self):
        s = SiteSettings.load()
        s.address = ADDRESS
        s.work_hours = "Пн–Пт 10:00–18:00, Сб–Нд — вихідний"
        s.map_embed_url = f"https://maps.google.com/maps?q={quote(ADDRESS)}&z=15&output=embed"
        s.iban_details = (
            "Отримувач: ФОП Бондарчук Є.П.\n"
            "IBAN: UA513052990000026008016222361\n"
            "ІПН: 2895713018\n"
            "Призначення платежу: оплата за замовлення №{номер}"
        )
        s.about_short = (
            "Premier Parts — інтернет-магазин нових кузовних запчастин для легкових авто: оптика, кузовні "
            "деталі, радіатори, автоскло й дзеркала. Працюємо з перевіреними виробниками FPS, TYC, DEPO, NRF, "
            "Nissens і відправляємо Новою Поштою по всій Україні, а в Києві — самовивіз і таксі."
        )
        s.seo_title = "Premier Parts — кузовні запчастини з доставкою по Україні"
        s.seo_description = (
            "Фари, ліхтарі, бампери, крила, радіатори, скло та дзеркала для 50+ марок авто. Пошук за VIN, "
            "артикулом і OEM-номером. Доставка Новою Поштою, самовивіз у Києві."
        )
        s.socials = {"viber": "viber://chat?number=%2B380634203993", "telegram": ""}
        s.save()

    def popular_makes(self):
        makes = Make.objects.annotate(
            n=Count("models__generations__fitments__product", filter=Q(models__generations__fitments__product__is_active=True), distinct=True)
        ).order_by("-n")
        top = [m.id for m in makes[:16] if m.n]
        Make.objects.update(is_popular=False)
        Make.objects.filter(id__in=top).update(is_popular=True)
        for sort, make_id in enumerate(top):
            Make.objects.filter(id=make_id).update(sort=sort)
        self.stdout.write(f"Популярних марок: {len(top)}")

    def featured(self) -> list[Product]:
        Product.objects.update(is_featured=False)
        candidates = (
            Product.objects.filter(is_active=True, price__gt=0, stock_status=StockStatus.IN_STOCK, images__isnull=False)
            .exclude(fitments__isnull=True)
            .select_related("category")
            .distinct()
            .order_by("-popularity")
        )
        by_category: dict[int, list[Product]] = {}
        for p in candidates[:600]:
            by_category.setdefault(p.category_id, []).append(p)
        chosen: list[Product] = []
        while len(chosen) < 16 and any(by_category.values()):
            for items in by_category.values():
                if items and len(chosen) < 16:
                    chosen.append(items.pop(0))
        Product.objects.filter(id__in=[p.id for p in chosen]).update(is_featured=True)
        self.stdout.write(f"Хітів продажу: {len(chosen)}")
        return chosen

    def promotions(self) -> dict[str, Promotion]:
        now = timezone.now()
        spec = [
            ("optika-15", "−15% на всю оптику", 15, "optika", "Фари, ліхтарі, протитуманки й покажчики поворотів від TYC, DEPO та FPS."),
            ("radiatory-10", "−10% на радіатори", 10, "radiatory-avtomobilnye", "Радіатори охолодження, кондиціонера й пічки для 50+ марок."),
            ("dzerkala-7", "Дзеркала −7%", 7, "zerkala-bokovye", "Дзеркала в зборі, вкладиші та кришки дзеркал."),
        ]
        result = {}
        for sort, (slug, title, percent, category_slug, description) in enumerate(spec):
            promo, _ = Promotion.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "discount_percent": percent,
                    "description": description,
                    "starts_at": now - timedelta(days=1),
                    "ends_at": now + timedelta(days=30),
                    "is_active": True,
                    "sort": sort,
                },
            )
            category = Category.objects.filter(slug=category_slug).first()
            if category:
                promo.categories.set([category])
            result[slug] = promo
        self.stdout.write(f"Акцій: {len(result)}")
        return result

    def _image_from(self, category_slug: str, featured: list[Product]) -> str:
        pool = [p for p in featured if p.category.slug == category_slug or (p.category.parent and p.category.parent.slug == category_slug)]
        if not pool:
            pool = list(
                Product.objects.filter(Q(category__slug=category_slug) | Q(category__parent__slug=category_slug), images__isnull=False, price__gt=0)
                .order_by("-popularity")[:1]
            )
        product = pool[0] if pool else None
        image = product.images.first() if product else None
        return image.image.name if image else ""

    def banners(self, promos, featured):
        Banner.objects.all().delete()
        spec = [
            {
                "placement": Banner.Placement.BENTO,
                "theme": Banner.Theme.DARK,
                "eyebrow": "РОЗПРОДАЖ ТИЖНЯ",
                "title": "−15% на всю оптику",
                "subtitle": "Фари, ліхтарі та протитуманки TYC і DEPO",
                "link": "/promotions/optika-15",
                "cta_label": "Дивитися акцію",
                "image": self._image_from("optika", featured),
            },
            {
                "placement": Banner.Placement.HOME_STRIP,
                "theme": Banner.Theme.GOLD,
                "eyebrow": "ПІДБІР ЗА VIN",
                "title": "Не впевнені, яка деталь підійде?",
                "subtitle": "Введіть VIN — визначимо авто й покажемо лише сумісні запчастини",
                "link": "/vin",
                "cta_label": "Перевірити VIN",
                "sort": 1,
            },
            {
                "placement": Banner.Placement.HOME_STRIP,
                "theme": Banner.Theme.DARK,
                "eyebrow": "−10% НА РАДІАТОРИ",
                "title": "Радіатори охолодження та кондиціонера",
                "subtitle": "NRF, Nissens, FPS — для 50+ марок авто",
                "link": "/promotions/radiatory-10",
                "cta_label": "До акції",
                "image": self._image_from("radiatory-avtomobilnye", featured),
                "sort": 2,
            },
            {
                "placement": Banner.Placement.CATALOG_TOP,
                "theme": Banner.Theme.DARK,
                "eyebrow": "АКЦІЯ",
                "title": "Дзеркала −7%",
                "subtitle": "Дзеркала в зборі, вкладиші та кришки",
                "link": "/promotions/dzerkala-7",
                "cta_label": "Дивитися",
                "image": self._image_from("zerkala-bokovye", featured),
            },
            {
                "placement": Banner.Placement.PRODUCT_SIDE,
                "theme": Banner.Theme.GOLD,
                "eyebrow": "КОНСУЛЬТАЦІЯ",
                "title": "Сумніваєтесь щодо сумісності?",
                "subtitle": "Надішліть VIN — менеджер підбере деталь і передзвонить",
                "link": "/vin",
                "cta_label": "Запит за VIN",
            },
        ]
        for item in spec:
            Banner.objects.create(**item)
        self.stdout.write(f"Банерів: {len(spec)}")

    def synonyms(self):
        for term, synonyms in SYNONYMS.items():
            SearchSynonym.objects.update_or_create(term=term, defaults={"synonyms": synonyms, "is_active": True})
        self.stdout.write(f"Синонімів: {len(SYNONYMS)}")
