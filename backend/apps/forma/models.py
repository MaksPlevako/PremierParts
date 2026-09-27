from django.conf import settings
from django.db import models


class FormaCategory(models.Model):
    external_id = models.PositiveBigIntegerField(unique=True)
    category = models.OneToOneField("catalog.Category", on_delete=models.PROTECT, related_name="forma_link")
    title = models.CharField(max_length=160)
    item_group = models.CharField(max_length=160, blank=True)
    item_sub_group = models.CharField(max_length=160, blank=True)
    is_leaf = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    raw_data = models.JSONField(default=dict)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.external_id}: {self.title}"


class FormaItem(models.Model):
    item_no = models.CharField(max_length=80)
    normalized_item_no = models.CharField(max_length=80, unique=True)
    product = models.OneToOneField("catalog.Product", on_delete=models.PROTECT, related_name="forma_item")
    category = models.ForeignKey(FormaCategory, on_delete=models.PROTECT, related_name="items")
    supplier_customer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity_raw = models.CharField(max_length=40, blank=True)
    in_stock = models.BooleanField(default=False)
    discontinued = models.BooleanField(default=False)
    short_text = models.TextField(blank=True)
    search_description = models.TextField(blank=True)
    criteria_line = models.TextField(blank=True)
    raw_data = models.JSONField(default=dict)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.item_no


class FormaAttributeName(models.Model):
    normalized_name = models.CharField(max_length=160, unique=True)
    name = models.CharField(max_length=160)

    def __str__(self):
        return self.name


class FormaItemAttribute(models.Model):
    item = models.ForeignKey(FormaItem, on_delete=models.CASCADE, related_name="attributes")
    attribute = models.ForeignKey(FormaAttributeName, on_delete=models.PROTECT)
    value = models.TextField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["item", "attribute"], name="forma_item_attribute_unique")]


class FormaWarehouseStock(models.Model):
    item = models.ForeignKey(FormaItem, on_delete=models.CASCADE, related_name="warehouses")
    location_code = models.CharField(max_length=120)
    location_name = models.CharField(max_length=120, blank=True)
    quantity_raw = models.CharField(max_length=40, blank=True)
    quantity_min = models.PositiveIntegerField(null=True, blank=True)
    quantity_is_more_than = models.BooleanField(default=False)
    reserved_raw = models.CharField(max_length=40, blank=True)
    raw_data = models.JSONField(default=dict)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["item", "location_code"], name="forma_item_warehouse_unique")]


class FormaVehicleType(models.Model):
    key = models.CharField(max_length=240, unique=True)
    external_type_id = models.PositiveBigIntegerField(null=True, blank=True, db_index=True)
    generation = models.OneToOneField("catalog.Generation", on_delete=models.PROTECT, related_name="forma_type")
    type_name = models.CharField(max_length=120, blank=True)
    type_range = models.CharField(max_length=120, blank=True)
    specs = models.JSONField(default=dict)
    raw_data = models.JSONField(default=dict)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.generation.full_label


class FormaVehicleFitment(models.Model):
    item = models.ForeignKey(FormaItem, on_delete=models.CASCADE, related_name="vehicle_fitments")
    vehicle = models.ForeignKey(FormaVehicleType, on_delete=models.PROTECT, related_name="item_fitments")
    raw_data = models.JSONField(default=dict)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["item", "vehicle"], name="forma_item_vehicle_unique")]


class FormaSyncJob(models.Model):
    class Mode(models.TextChoices):
        FULL = "full", "Повна"
        FAST = "fast", "Швидка"

    class Status(models.TextChoices):
        PENDING = "pending", "Очікує"
        RUNNING = "running", "Виконується"
        COMPLETED = "completed", "Завершено"
        WITH_ERRORS = "completed_with_errors", "Завершено з помилками"
        FAILED = "failed", "Помилка"

    mode = models.CharField(max_length=8, choices=Mode.choices)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING, db_index=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    heartbeat_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    categories_processed = models.PositiveIntegerField(default=0)
    products_processed = models.PositiveIntegerField(default=0)
    products_created = models.PositiveIntegerField(default=0)
    products_updated = models.PositiveIntegerField(default=0)
    vehicles_processed = models.PositiveIntegerField(default=0)
    fitments_created = models.PositiveIntegerField(default=0)
    errors_count = models.PositiveIntegerField(default=0)
    errors = models.JSONField(default=list)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Forma {self.mode} #{self.pk} ({self.status})"
