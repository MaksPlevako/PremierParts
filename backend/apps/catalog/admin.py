from django.contrib import admin, messages
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    ChoicesDropdownFilter,
    RangeNumericFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from unfold.decorators import action, display

from .models import (
    CarModel,
    Category,
    Fitment,
    Generation,
    Make,
    Manufacturer,
    PartNumber,
    Product,
    ProductImage,
    StockStatus,
)


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image", "alt", "sort")
    tab = True
    verbose_name_plural = _("Фото")


class PartNumberInline(TabularInline):
    model = PartNumber
    extra = 0
    fields = ("number", "kind")
    tab = True


class FitmentInline(TabularInline):
    model = Fitment
    extra = 0
    autocomplete_fields = ["generation"]
    tab = True


class ProductResource(resources.ModelResource):
    """CSV/XLSX import-export for bulk price and stock updates."""

    manufacturer = fields.Field(attribute="manufacturer__name", column_name="manufacturer", readonly=True)
    category = fields.Field(attribute="category__name", column_name="category", readonly=True)

    class Meta:
        model = Product
        fields = ("id", "sku", "name", "manufacturer", "category", "price", "old_price", "stock_status", "is_active", "is_featured")
        export_order = fields
        import_id_fields = ("id",)
        skip_unchanged = True
        report_skipped = False


@admin.register(Product)
class ProductAdmin(ModelAdmin, TranslationAdmin, ImportExportModelAdmin):
    resource_classes = [ProductResource]
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ("product", "manufacturer", "category", "price", "stock_status", "is_featured", "is_active")
    list_display_links = ("product",)
    list_editable = ("price", "stock_status")
    list_filter = (
        ("category", RelatedDropdownFilter),
        ("manufacturer", RelatedDropdownFilter),
        ("stock_status", ChoicesDropdownFilter),
        ("price", RangeNumericFilter),
        "is_featured",
        "is_active",
    )
    list_filter_submit = True
    list_per_page = 50
    search_fields = ("name_uk", "sku", "part_numbers__normalized")
    search_help_text = _("Пошук за назвою, артикулом або OEM-номером")
    autocomplete_fields = ("category", "manufacturer")
    readonly_fields = ("created_at", "updated_at", "legacy_url")
    prepopulated_fields = {"slug": ("name_uk",)}
    inlines = [ProductImageInline, PartNumberInline, FitmentInline]
    actions = ["make_featured", "remove_featured", "deactivate", "mark_in_stock"]
    fieldsets = (
        (None, {"fields": ("name", "slug", "category", "manufacturer", "sku")}),
        (_("Ціна та наявність"), {"fields": (("price", "old_price"), "stock_status", ("is_active", "is_featured"), "popularity")}),
        (_("Характеристики"), {"fields": (("side", "position"), "condition", "description")}),
        (_("Службове"), {"classes": ["collapse"], "fields": ("legacy_url", "created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category", "manufacturer").prefetch_related("images")

    @display(description=_("Товар"), header=True, ordering="name_uk")
    def product(self, obj):
        first = next(iter(obj.images.all()), None)
        subtitle = " · ".join(filter(None, [obj.sku, obj.get_stock_status_display()]))
        image = {"path": first.image.url, "width": 64, "height": 48, "squared": True} if first and first.image else None
        return [obj.name, subtitle, None, image] if image else [obj.name, subtitle]

    @action(description=_("Позначити як хіт продажу"))
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, _("Позначено як хіт: %d") % updated, messages.SUCCESS)

    @action(description=_("Прибрати з хітів"))
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)

    @action(description=_("Зняти з продажу"))
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)

    @action(description=_("Позначити «В наявності»"))
    def mark_in_stock(self, request, queryset):
        queryset.update(stock_status=StockStatus.IN_STOCK)


@admin.register(Category)
class CategoryAdmin(ModelAdmin, TranslationAdmin):
    list_display = ("name", "parent", "slug", "icon", "product_total", "sort", "is_active")
    list_editable = ("sort", "is_active")
    list_filter = ("parent", "is_active")
    search_fields = ("name_uk", "slug")
    prepopulated_fields = {"slug": ("name_uk",)}

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent").annotate(n=Count("products"))

    @display(description=_("Товарів"), ordering="n")
    def product_total(self, obj):
        return obj.n


class CarModelInline(TabularInline):
    model = CarModel
    extra = 0
    fields = ("name", "family", "market", "slug")
    show_change_link = True


@admin.register(Make)
class MakeAdmin(ModelAdmin):
    list_display = ("name", "slug", "is_popular", "sort", "model_total")
    list_editable = ("is_popular", "sort")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [CarModelInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(n=Count("models"))

    @display(description=_("Моделей"), ordering="n")
    def model_total(self, obj):
        return obj.n


class GenerationInline(TabularInline):
    model = Generation
    extra = 0
    fields = ("year_from", "year_to", "slug")


@admin.register(CarModel)
class CarModelAdmin(ModelAdmin):
    list_display = ("name", "make", "family", "market")
    list_filter = (("make", RelatedDropdownFilter), "market")
    search_fields = ("name", "family", "make__name")
    autocomplete_fields = ("make",)
    inlines = [GenerationInline]


@admin.register(Generation)
class GenerationAdmin(ModelAdmin):
    list_display = ("full_label", "year_from", "year_to", "product_total")
    list_filter = (("model__make", RelatedDropdownFilter),)
    search_fields = ("model__name", "model__family", "model__make__name")
    autocomplete_fields = ("model",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("model__make").annotate(n=Count("fitments"))

    @display(description=_("Авто"), ordering="model__name")
    def full_label(self, obj):
        return obj.full_label

    @display(description=_("Товарів"), ordering="n")
    def product_total(self, obj):
        return obj.n


@admin.register(Manufacturer)
class ManufacturerAdmin(ModelAdmin):
    list_display = ("name", "country", "product_total")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(n=Count("products"))

    @display(description=_("Товарів"), ordering="n")
    def product_total(self, obj):
        return obj.n
