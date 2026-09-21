from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def _default_phones():
    return [
        {"number": "+380634203993", "label": "(063) 420-39-93", "viber": True},
        {"number": "+380980701434", "label": "(098) 070-14-34", "viber": False},
    ]


class SiteSettings(models.Model):
    """Singleton with contacts and shop-wide texts, editable in the admin."""

    phones = models.JSONField(_("телефони"), default=_default_phones, help_text=_('Список: {"number","label","viber"}'))
    email = models.EmailField(_("email"), default="info@premier-parts.com.ua")
    address = models.CharField(_("адреса"), max_length=255, default="Київ, вул. Вікентія Беретті, 6Б")
    work_hours = models.CharField(_("графік роботи"), max_length=255, default="Пн–Пт 10:00–18:00")
    map_embed_url = models.URLField(_("посилання для карти (embed)"), max_length=1000, blank=True)
    socials = models.JSONField(_("соцмережі"), default=dict, blank=True, help_text=_('{"telegram": "...", "instagram": "..."}'))
    iban_details = models.TextField(_("реквізити для оплати"), blank=True)
    pickup_note = models.CharField(
        _("умови самовивозу"), max_length=255, default="Завдаток 300 грн входить у вартість товару"
    )
    about_short = models.TextField(_("коротко про компанію"), blank=True)
    seo_title = models.CharField(_("SEO title"), max_length=255, blank=True)
    seo_description = models.TextField(_("SEO description"), blank=True)

    class Meta:
        verbose_name = _("налаштування сайту")
        verbose_name_plural = _("налаштування сайту")

    def __str__(self):
        return str(_("Налаштування сайту"))

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "SiteSettings":
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj


class LiveQuerySet(models.QuerySet):
    def live(self):
        now = timezone.now()
        return self.filter(is_active=True).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now),
            Q(ends_at__isnull=True) | Q(ends_at__gte=now),
        )


class Banner(models.Model):
    class Placement(models.TextChoices):
        HERO = "hero", _("Головна — під пошуком")
        BENTO = "bento", _("Головна — бенто (велика акція)")
        HOME_STRIP = "home_strip", _("Головна — рекламна смуга")
        CATALOG_TOP = "catalog_top", _("Каталог — над товарами")
        PRODUCT_SIDE = "product_side", _("Картка товару — збоку")

    class Theme(models.TextChoices):
        DARK = "dark", _("Графіт")
        LIGHT = "light", _("Платина")
        GOLD = "gold", _("Золото")

    title = models.CharField(_("заголовок"), max_length=160)
    subtitle = models.CharField(_("підзаголовок"), max_length=255, blank=True)
    eyebrow = models.CharField(_("надпис над заголовком"), max_length=60, blank=True)
    image = models.ImageField(_("зображення"), upload_to="banners/", blank=True)
    image_mobile = models.ImageField(_("зображення для мобільного"), upload_to="banners/", blank=True)
    link = models.CharField(_("посилання"), max_length=300, blank=True)
    cta_label = models.CharField(_("текст кнопки"), max_length=60, blank=True)
    placement = models.CharField(_("місце показу"), max_length=20, choices=Placement.choices, default=Placement.BENTO)
    theme = models.CharField(_("тема"), max_length=10, choices=Theme.choices, default=Theme.DARK)
    starts_at = models.DateTimeField(_("показувати з"), null=True, blank=True)
    ends_at = models.DateTimeField(_("показувати до"), null=True, blank=True)
    sort = models.PositiveIntegerField(_("порядок"), default=100)
    is_active = models.BooleanField(_("активний"), default=True)

    objects = LiveQuerySet.as_manager()

    class Meta:
        ordering = ["placement", "sort", "-id"]
        verbose_name = _("банер")
        verbose_name_plural = _("банери та реклама")

    def __str__(self):
        return self.title


class Promotion(models.Model):
    title = models.CharField(_("назва"), max_length=160)
    slug = models.SlugField(max_length=160, unique=True)
    description = models.TextField(_("опис"), blank=True)
    discount_percent = models.PositiveSmallIntegerField(_("знижка, %"), default=0)
    image = models.ImageField(_("зображення"), upload_to="promotions/", blank=True)
    starts_at = models.DateTimeField(_("початок"), null=True, blank=True)
    ends_at = models.DateTimeField(_("кінець"), null=True, blank=True)
    categories = models.ManyToManyField("catalog.Category", blank=True, verbose_name=_("категорії"))
    manufacturers = models.ManyToManyField("catalog.Manufacturer", blank=True, verbose_name=_("виробники"))
    products = models.ManyToManyField("catalog.Product", blank=True, verbose_name=_("товари"))
    is_active = models.BooleanField(_("активна"), default=True)
    sort = models.PositiveIntegerField(_("порядок"), default=100)

    objects = LiveQuerySet.as_manager()

    class Meta:
        ordering = ["sort", "-discount_percent"]
        verbose_name = _("акція")
        verbose_name_plural = _("акції")

    def __str__(self):
        return self.title


class Page(models.Model):
    title = models.CharField(_("заголовок"), max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    body = models.TextField(_("текст"), blank=True)
    seo_title = models.CharField(_("SEO title"), max_length=255, blank=True)
    seo_description = models.TextField(_("SEO description"), blank=True)
    show_in_footer = models.BooleanField(_("показувати у футері"), default=True)
    sort = models.PositiveIntegerField(_("порядок"), default=100)
    is_active = models.BooleanField(_("опублікована"), default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort", "title"]
        verbose_name = _("сторінка")
        verbose_name_plural = _("сторінки")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"/page/{self.slug}"
