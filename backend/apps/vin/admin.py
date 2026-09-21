from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import display

from .models import VinRequest, Wmi


@admin.register(VinRequest)
class VinRequestAdmin(ModelAdmin):
    list_display = ("vin", "car", "part_query", "name", "phone", "status_badge", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("vin", "phone", "name", "part_query")
    readonly_fields = ("vin", "decoded", "created_at")
    fields = ("status", "vin", "name", "phone", "part_query", "comment", "manager_note", "decoded", "created_at")
    list_editable = ()

    @display(description=_("Статус"), label={"new": "warning", "in_progress": "info", "done": "success"})
    def status_badge(self, obj):
        return obj.status, obj.get_status_display()

    @display(description=_("Авто"))
    def car(self, obj):
        matches = (obj.decoded or {}).get("matches") or []
        if matches:
            return matches[0].get("full_label")
        d = obj.decoded or {}
        return " ".join(str(x) for x in (d.get("make"), d.get("model"), d.get("year")) if x) or "—"


@admin.register(Wmi)
class WmiAdmin(ModelAdmin):
    list_display = ("code", "make_name", "country")
    search_fields = ("code", "make_name")
