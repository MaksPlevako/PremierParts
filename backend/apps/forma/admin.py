from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    FormaAttributeName, FormaCategory, FormaItem, FormaItemAttribute,
    FormaSyncJob, FormaVehicleFitment, FormaVehicleType, FormaWarehouseStock,
)


@admin.register(FormaSyncJob)
class FormaSyncJobAdmin(ModelAdmin):
    list_display = (
        "id", "mode", "status", "created_at", "started_at", "finished_at",
        "categories_processed", "products_processed", "products_created", "vehicles_processed", "errors_count",
    )
    list_filter = ("mode", "status")
    readonly_fields = (
        "status", "requested_by", "created_at", "started_at", "heartbeat_at", "finished_at",
        "categories_processed", "products_processed", "products_created", "products_updated",
        "vehicles_processed", "fitments_created", "errors_count", "errors",
    )

    def get_fields(self, request, obj=None):
        return ("mode",) if obj is None else ("mode", *self.readonly_fields)

    def has_change_permission(self, request, obj=None):
        return False if obj is not None else super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            obj.requested_by = request.user
            obj.status = FormaSyncJob.Status.PENDING
        super().save_model(request, obj, form, change)


@admin.register(FormaCategory)
class FormaCategoryAdmin(ModelAdmin):
    list_display = ("external_id", "title", "category", "is_leaf", "active", "last_seen_at")
    search_fields = ("external_id", "title")
    readonly_fields = ("external_id", "category", "title", "item_group", "item_sub_group", "is_leaf", "active", "raw_data", "last_seen_at")


@admin.register(FormaItem)
class FormaItemAdmin(ModelAdmin):
    list_display = ("item_no", "product", "category", "retail_price", "in_stock", "last_seen_at")
    search_fields = ("item_no", "normalized_item_no", "product__name")
    readonly_fields = [field.name for field in FormaItem._meta.fields]


@admin.register(FormaVehicleType)
class FormaVehicleTypeAdmin(ModelAdmin):
    list_display = ("key", "generation", "external_type_id", "type_name", "last_seen_at")
    search_fields = ("key", "type_name")
    readonly_fields = [field.name for field in FormaVehicleType._meta.fields]


for model in (FormaAttributeName, FormaItemAttribute, FormaWarehouseStock, FormaVehicleFitment):
    admin.site.register(model, ModelAdmin)
