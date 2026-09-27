from django.contrib import admin
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RangeDateFilter
from unfold.decorators import display

from .models import Order, OrderItem
from .notify import notify_order_status

STATUS_COLORS = {
    "new": "warning",
    "confirmed": "info",
    "shipped": "primary",
    "completed": "success",
    "canceled": "danger",
}


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    fields = ("name", "sku", "price", "old_price", "qty", "line_total")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ("number", "status_badge", "kind_badge", "customer", "delivery_method", "total", "car", "created_at")
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("delivery_method", ChoicesDropdownFilter),
        "kind",
        ("created_at", RangeDateFilter),
    )
    list_filter_submit = True
    search_fields = ("number", "tracking_number", "phone", "customer_name", "email", "items__sku")
    readonly_fields = ("number", "kind", "subtotal", "discount", "total", "car_label", "created_at", "updated_at")
    inlines = [OrderItemInline]

    def save_model(self, request, obj, form, change):
        previous = Order.objects.filter(pk=obj.pk).values("status", "tracking_number").first() if change else None
        super().save_model(request, obj, form, change)
        if previous and (previous["status"] != obj.status or previous["tracking_number"] != obj.tracking_number):
            transaction.on_commit(lambda order_id=obj.pk: notify_order_status(Order.objects.get(pk=order_id)), robust=True)
    fieldsets = (
        (_("Статус"), {"fields": ("number", "status", "kind", "manager_note")}),
        (_("Клієнт"), {"fields": ("customer_name", "phone", "email", "car_label", "comment")}),
        (_("Доставка та оплата"), {"fields": ("delivery_method", "city", "np_branch", "address", "tracking_number", "payment_method")}),
        (_("Суми"), {"fields": ("subtotal", "discount", "total", "created_at", "updated_at")}),
    )

    @display(description=_("Статус"), label=STATUS_COLORS)
    def status_badge(self, obj):
        return obj.status, obj.get_status_display()

    @display(description=_("Тип"), label={"quick": "info", "regular": "success"})
    def kind_badge(self, obj):
        return obj.kind, obj.get_kind_display()

    @display(description=_("Клієнт"), header=True)
    def customer(self, obj):
        return obj.customer_name or "—", obj.phone

    @display(description=_("Авто клієнта"))
    def car(self, obj):
        return (obj.car_snapshot or {}).get("full_label", "—")

    @display(description=_("Авто клієнта («Моє авто»)"))
    def car_label(self, obj):
        return (obj.car_snapshot or {}).get("full_label", "—")
