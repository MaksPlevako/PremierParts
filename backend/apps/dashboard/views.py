from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

from apps.catalog.models import Product
from apps.orders.models import Order
from apps.vin.models import VinRequest


def _money(value) -> str:
    return f"{value or 0:,.0f}".replace(",", " ") + " ₴"


def dashboard_callback(request, context):
    now = timezone.localtime()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week = today - timedelta(days=6)

    orders_today = Order.objects.filter(created_at__gte=today).exclude(status=Order.Status.CANCELED)
    orders_week = Order.objects.filter(created_at__gte=week).exclude(status=Order.Status.CANCELED)
    today_stats = orders_today.aggregate(n=Count("id"), total=Sum("total"))
    week_stats = orders_week.aggregate(n=Count("id"), total=Sum("total"))
    products = Product.objects.aggregate(
        active=Count("id", filter=Q(is_active=True), distinct=True),
        no_price=Count("id", filter=Q(is_active=True, price=0), distinct=True),
        no_photo=Count("id", filter=Q(is_active=True, images__isnull=True), distinct=True),
    )
    new_vin = VinRequest.objects.filter(status=VinRequest.Status.NEW).count()

    context.update(
        {
            "kpis": [
                {
                    "title": "Замовлення сьогодні",
                    "value": today_stats["n"],
                    "footer": _money(today_stats["total"]),
                    "icon": "shopping_bag",
                    "href": reverse("admin:orders_order_changelist") + f"?created_at_from={today.date().isoformat()}",
                },
                {
                    "title": "За 7 днів",
                    "value": week_stats["n"],
                    "footer": _money(week_stats["total"]),
                    "icon": "trending_up",
                    "href": reverse("admin:orders_order_changelist"),
                },
                {
                    "title": "Нові запити за VIN",
                    "value": new_vin,
                    "footer": "очікують відповіді",
                    "icon": "qr_code_scanner",
                    "href": reverse("admin:vin_vinrequest_changelist") + "?status__exact=new",
                },
                {
                    "title": "Товарів у продажу",
                    "value": f"{products['active']:,}".replace(",", " "),
                    "footer": f"без ціни: {products['no_price']} · без фото: {products['no_photo']}",
                    "icon": "inventory_2",
                    "href": reverse("admin:catalog_product_changelist"),
                },
            ],
            "recent_orders": {
                "headers": ["Номер", "Клієнт", "Авто", "Сума", "Статус", "Створено"],
                "rows": [
                    [
                        f'<a class="pp-link" href="{reverse("admin:orders_order_change", args=[o.id])}">{o.number}</a>',
                        f"{o.customer_name or '—'}<br><span class='pp-muted'>{o.phone}</span>",
                        (o.car_snapshot or {}).get("full_label", "—"),
                        _money(o.total),
                        f'<span class="pp-status pp-status--{o.status}">{o.get_status_display()}</span>',
                        date_format(timezone.localtime(o.created_at), "d.m H:i"),
                    ]
                    for o in Order.objects.all()[:8]
                ],
            },
            "recent_vin": {
                "headers": ["VIN", "Деталь", "Телефон", "Створено"],
                "rows": [
                    [
                        f'<a class="pp-link" href="{reverse("admin:vin_vinrequest_change", args=[r.id])}">{r.vin}</a>',
                        r.part_query or "—",
                        r.phone,
                        date_format(timezone.localtime(r.created_at), "d.m H:i"),
                    ]
                    for r in VinRequest.objects.filter(status=VinRequest.Status.NEW)[:6]
                ],
            },
            "quick_links": [
                {"title": "Новий банер", "icon": "add_photo_alternate", "href": reverse("admin:content_banner_add")},
                {"title": "Нова акція", "icon": "percent", "href": reverse("admin:content_promotion_add")},
                {"title": "Імпорт прайсу постачальника", "icon": "upload_file", "href": reverse("admin:catalog_product_supplier_price_import")},
                {"title": "Переіндексувати пошук", "icon": "sync", "href": reverse("admin:search_searchsynonym_reindex")},
                {"title": "Відкрити сайт", "icon": "open_in_new", "href": "/"},
            ],
        }
    )
    return context
