import re

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.normalize import normalize_part_number

_GENERATION_MARKERS = {"USA", "US", "EU", "EUR", "JDM", "ASIA", "UA"}


class Market(models.TextChoices):
    EU = "eu", _("Європа")
    USA = "usa", _("США")
    ASIA = "asia", _("Азія")
    OTHER = "other", _("Не вказано")


class Make(models.Model):
    name = models.CharField(_("назва"), max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    logo = models.ImageField(_("логотип"), upload_to="makes/", blank=True)
    is_popular = models.BooleanField(_("популярна"), default=False)
    sort = models.PositiveIntegerField(_("порядок"), default=100)
    legacy_id = models.PositiveIntegerField(null=True, blank=True, unique=True)

    class Meta:
        ordering = ["sort", "name"]
        verbose_name = _("марка авто")
        verbose_name_plural = _("марки авто")

    def __str__(self):
        return self.name


class CarModel(models.Model):
    make = models.ForeignKey(Make, on_delete=models.CASCADE, related_name="models", verbose_name=_("марка"))
    name = models.CharField(_("назва"), max_length=120)
    family = models.CharField(_("сімейство"), max_length=80, blank=True, help_text=_("Напр. «Passat» для «Passat B7 USA»"))
    market = models.CharField(_("ринок"), max_length=8, choices=Market.choices, default=Market.OTHER)
    slug = models.SlugField(max_length=140)
    legacy_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["make__name", "name"]
        unique_together = [("make", "slug")]
        verbose_name = _("модель")
        verbose_name_plural = _("моделі")

    def __str__(self):
        return f"{self.make.name} {self.name}"

    @staticmethod
    def derive_family(name: str) -> str:
        tokens = name.split()
        if not tokens:
            return ""
        family = [tokens[0]]
        for token in tokens[1:]:
            has_digit = any(ch.isdigit() for ch in token)
            short_code = len(token) <= 3 and token.isupper()
            if has_digit or short_code or token.upper() in _GENERATION_MARKERS:
                break
            family.append(token)
        return " ".join(family)

    @staticmethod
    def derive_market(name: str) -> str:
        tokens = {t.upper() for t in re.split(r"[\s\-/()]+", name) if t}
        if tokens & {"USA", "US"}:
            return Market.USA
        if tokens & {"EU", "EUR", "EUROPE"}:
            return Market.EU
        if tokens & {"JDM", "ASIA", "JAPAN"}:
            return Market.ASIA
        return Market.OTHER

    def save(self, *args, **kwargs):
        if not self.family:
            self.family = self.derive_family(self.name)
        if self.market == Market.OTHER:
            self.market = self.derive_market(self.name)
        super().save(*args, **kwargs)


class Generation(models.Model):
    """A model's production series (years). Parts are fitted to generations."""

    model = models.ForeignKey(CarModel, on_delete=models.CASCADE, related_name="generations", verbose_name=_("модель"))
    year_from = models.PositiveSmallIntegerField(_("рік від"), null=True, blank=True)
    year_to = models.PositiveSmallIntegerField(_("рік до"), null=True, blank=True, help_text=_("Порожньо — випускається досі"))
    source_label = models.CharField(_("назва типу з джерела"), max_length=120, blank=True)
    slug = models.SlugField(max_length=40)
    legacy_id = models.CharField(max_length=40, blank=True, db_index=True)

    class Meta:
        ordering = ["model__make__name", "model__name", "year_from"]
        unique_together = [("model", "slug")]
        verbose_name = _("серія (роки)")
        verbose_name_plural = _("серії (роки)")

    def __str__(self):
        return self.full_label

    @property
    def market(self) -> str:
        return self.model.market

    @property
    def years_label(self) -> str:
        if self.year_from and self.year_to:
            return f"{self.year_from}–{self.year_to}"
        if self.year_from:
            return f"{self.year_from}–"
        if self.year_to:
            return f"–{self.year_to}"
        return ""

    @property
    def label(self) -> str:
        years = self.years_label
        detail = years or self.source_label
        return f"{self.model.name} ({detail})" if detail else self.model.name

    @property
    def full_label(self) -> str:
        return f"{self.model.make.name} {self.label}"

    def covers_year(self, year: int) -> bool:
        if self.year_from and year < self.year_from:
            return False
        if self.year_to and year > self.year_to:
            return False
        return True


class Category(models.Model):
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children", verbose_name=_("батьківська")
    )
    name = models.CharField(_("назва"), max_length=160)
    slug = models.SlugField(max_length=160, unique=True)
    icon = models.CharField(
        _("іконка"),
        max_length=32,
        blank=True,
        help_text=_("Ключ іконки: light, body, radiator, mirror, glass, exhaust, door, bumper…"),
    )
    image = models.ImageField(_("зображення"), upload_to="categories/", blank=True)
    description = models.TextField(_("опис"), blank=True)
    sort = models.PositiveIntegerField(_("порядок"), default=100)
    is_active = models.BooleanField(_("активна"), default=True)

    class Meta:
        ordering = ["sort", "name"]
        verbose_name = _("категорія")
        verbose_name_plural = _("категорії")

    def __str__(self):
        return f"{self.parent.name} → {self.name}" if self.parent_id else self.name


class Manufacturer(models.Model):
    name = models.CharField(_("назва"), max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    logo = models.ImageField(_("логотип"), upload_to="manufacturers/", blank=True)
    country = models.CharField(_("країна"), max_length=60, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("виробник деталей")
        verbose_name_plural = _("виробники деталей")

    def __str__(self):
        return self.name


class StockStatus(models.TextChoices):
    IN_STOCK = "in_stock", _("В наявності")
    ON_ORDER = "on_order", _("Під замовлення")
    OUT_OF_STOCK = "out_of_stock", _("Немає в наявності")


class Side(models.TextChoices):
    LEFT = "left", _("Ліва")
    RIGHT = "right", _("Права")
    BOTH = "both", _("Комплект")
    NONE = "none", _("—")


class Position(models.TextChoices):
    FRONT = "front", _("Передня")
    REAR = "rear", _("Задня")
    NONE = "none", _("—")


class Product(models.Model):
    name = models.CharField(_("назва"), max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    sku = models.CharField(_("артикул"), max_length=80, blank=True, db_index=True)
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.SET_NULL, null=True, blank=True, related_name="products", verbose_name=_("виробник")
    )
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products", verbose_name=_("категорія"))
    description = models.TextField(_("опис"), blank=True)
    price = models.DecimalField(_("ціна, ₴"), max_digits=10, decimal_places=2, default=0, help_text=_("0 — «Ціну уточнюйте»"))
    supplier_price = models.DecimalField(
        _("остання ціна постачальника, ₴"), max_digits=10, decimal_places=2, null=True, blank=True, editable=False
    )
    old_price = models.DecimalField(_("стара ціна, ₴"), max_digits=10, decimal_places=2, null=True, blank=True)
    stock_status = models.CharField(_("наявність"), max_length=16, choices=StockStatus.choices, default=StockStatus.IN_STOCK)
    side = models.CharField(_("сторона"), max_length=8, choices=Side.choices, default=Side.NONE)
    position = models.CharField(_("розташування"), max_length=8, choices=Position.choices, default=Position.NONE)
    condition = models.CharField(_("стан"), max_length=20, default="new")
    is_active = models.BooleanField(_("активний"), default=True)
    is_featured = models.BooleanField(_("хіт продажу"), default=False)
    popularity = models.PositiveIntegerField(_("популярність"), default=0)
    legacy_url = models.URLField(max_length=500, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-popularity", "name"]
        verbose_name = _("товар")
        verbose_name_plural = _("товари")
        indexes = [models.Index(fields=["is_active", "category"]), models.Index(fields=["is_featured"])]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/product/{self.slug}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(_("фото"), upload_to="products/%Y/")
    alt = models.CharField(max_length=300, blank=True)
    sort = models.PositiveIntegerField(default=0)
    source_url = models.URLField(max_length=500, blank=True)

    class Meta:
        ordering = ["sort", "id"]
        verbose_name = _("фото")
        verbose_name_plural = _("фото")

    def __str__(self):
        return self.image.name


class Fitment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="fitments")
    generation = models.ForeignKey(Generation, on_delete=models.CASCADE, related_name="fitments", verbose_name=_("авто"))

    class Meta:
        unique_together = [("product", "generation")]
        verbose_name = _("сумісність")
        verbose_name_plural = _("сумісність з авто")

    def __str__(self):
        return str(self.generation)


class PartNumberKind(models.TextChoices):
    SKU = "sku", _("Артикул")
    OEM = "oem", _("OEM")
    CROSS = "cross", _("Крос-номер")


class PartNumber(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="part_numbers")
    number = models.CharField(_("номер"), max_length=80)
    normalized = models.CharField(max_length=80, db_index=True, editable=False)
    kind = models.CharField(_("тип"), max_length=8, choices=PartNumberKind.choices, default=PartNumberKind.OEM)

    class Meta:
        unique_together = [("product", "normalized")]
        verbose_name = _("номер деталі")
        verbose_name_plural = _("номери деталі (артикул, OEM, кроси)")

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        self.normalized = normalize_part_number(self.number)
        super().save(*args, **kwargs)
