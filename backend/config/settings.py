import os
from pathlib import Path

import dj_database_url
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-secret-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080"
).split(",")

INSTALLED_APPS = [
    "modeltranslation",
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.import_export",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "import_export",
    "apps.core",
    "apps.catalog",
    "apps.content",
    "apps.search",
    "apps.vin",
    "apps.orders",
    "apps.importer",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL", "postgres://premier:premier@localhost:5432/premier"),
        conn_max_age=60,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "uk"
LANGUAGES = [("uk", "Українська")]
MODELTRANSLATION_DEFAULT_LANGUAGE = "uk"
MODELTRANSLATION_FALLBACK_LANGUAGES = ("uk",)
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", "/data/media"))
SERVE_MEDIA = env_bool("SERVE_MEDIA", True)
IMPORT_CACHE_DIR = Path(os.environ.get("IMPORT_CACHE_DIR", "/data/cache"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "UNAUTHENTICATED_USER": None,
}

# --- Integrations ---
MEILI_URL = os.environ.get("MEILI_URL", "http://localhost:7700")
MEILI_MASTER_KEY = os.environ.get("MEILI_MASTER_KEY", "dev-meili-master-key")
MEILI_INDEX = os.environ.get("MEILI_INDEX", "products")
NEXT_REVALIDATE_URL = os.environ.get("NEXT_REVALIDATE_URL", "")
REVALIDATE_SECRET = os.environ.get("REVALIDATE_SECRET", "dev-revalidate-secret")
NOVA_POSHTA_API_KEY = os.environ.get("NOVA_POSHTA_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
NHTSA_URL = os.environ.get("NHTSA_URL", "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json")
MANAGER_EMAILS = [e for e in os.environ.get("MANAGER_EMAILS", "info@premier-parts.com.ua").split(",") if e]
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = "Premier Parts <no-reply@premier-parts.com.ua>"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {"httpx": {"level": "WARNING"}, "httpcore": {"level": "WARNING"}},
}

# --- Admin (Unfold) ---
UNFOLD = {
    "SITE_TITLE": "Premier Parts",
    "SITE_HEADER": "Premier Parts",
    "SITE_SUBHEADER": "Адмін-панель магазину",
    "SITE_URL": "/",
    "SITE_SYMBOL": "directions_car",
    "SITE_LOGO": lambda request: static("admin/pp-logo.svg"),
    "SITE_ICON": lambda request: static("admin/pp-mark.svg"),
    "SITE_FAVICONS": [
        {"rel": "icon", "sizes": "32x32", "type": "image/svg+xml", "href": lambda request: static("admin/pp-mark.svg")},
    ],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "DASHBOARD_CALLBACK": "apps.dashboard.views.dashboard_callback",
    "STYLES": [lambda request: static("admin/pp-admin.css")],
    "BORDER_RADIUS": "10px",
    "COLORS": {
        "base": {
            "50": "oklch(98.5% 0.002 247)",
            "100": "oklch(96.7% 0.003 247)",
            "200": "oklch(92.8% 0.006 247)",
            "300": "oklch(87.2% 0.01 247)",
            "400": "oklch(70.7% 0.015 247)",
            "500": "oklch(55.1% 0.018 247)",
            "600": "oklch(44.6% 0.02 247)",
            "700": "oklch(37.3% 0.02 247)",
            "800": "oklch(27.8% 0.015 247)",
            "900": "oklch(21% 0.01 247)",
            "950": "oklch(13% 0.008 247)",
        },
        "primary": {
            "50": "oklch(98% 0.02 88)",
            "100": "oklch(95% 0.045 88)",
            "200": "oklch(90% 0.08 86)",
            "300": "oklch(85% 0.11 84)",
            "400": "oklch(79% 0.13 80)",
            "500": "oklch(71% 0.13 76)",
            "600": "oklch(62% 0.12 72)",
            "700": "oklch(53% 0.1 70)",
            "800": "oklch(44% 0.08 68)",
            "900": "oklch(37% 0.065 66)",
            "950": "oklch(26% 0.045 64)",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Огляд"),
                "items": [
                    {"title": _("Дашборд"), "icon": "dashboard", "link": reverse_lazy("admin:index")},
                ],
            },
            {
                "title": _("Продажі"),
                "items": [
                    {"title": _("Замовлення"), "icon": "shopping_bag", "link": reverse_lazy("admin:orders_order_changelist")},
                    {"title": _("Запити за VIN"), "icon": "qr_code_scanner", "link": reverse_lazy("admin:vin_vinrequest_changelist")},
                ],
            },
            {
                "title": _("Каталог"),
                "items": [
                    {"title": _("Товари"), "icon": "inventory_2", "link": reverse_lazy("admin:catalog_product_changelist")},
                    {"title": _("Категорії"), "icon": "category", "link": reverse_lazy("admin:catalog_category_changelist")},
                    {"title": _("Марки авто"), "icon": "directions_car", "link": reverse_lazy("admin:catalog_make_changelist")},
                    {"title": _("Моделі"), "icon": "garage", "link": reverse_lazy("admin:catalog_carmodel_changelist")},
                    {"title": _("Серії (роки)"), "icon": "calendar_month", "link": reverse_lazy("admin:catalog_generation_changelist")},
                    {"title": _("Виробники деталей"), "icon": "factory", "link": reverse_lazy("admin:catalog_manufacturer_changelist")},
                ],
            },
            {
                "title": _("Маркетинг"),
                "items": [
                    {"title": _("Банери та реклама"), "icon": "view_carousel", "link": reverse_lazy("admin:content_banner_changelist")},
                    {"title": _("Акції"), "icon": "percent", "link": reverse_lazy("admin:content_promotion_changelist")},
                ],
            },
            {
                "title": _("Контент"),
                "items": [
                    {"title": _("Сторінки"), "icon": "description", "link": reverse_lazy("admin:content_page_changelist")},
                    {"title": _("Налаштування сайту"), "icon": "settings", "link": reverse_lazy("admin:content_sitesettings_changelist")},
                ],
            },
            {
                "title": _("Пошук"),
                "items": [
                    {"title": _("Синоніми пошуку"), "icon": "manage_search", "link": reverse_lazy("admin:search_searchsynonym_changelist")},
                    {"title": _("Коди виробників (WMI)"), "icon": "pin", "link": reverse_lazy("admin:vin_wmi_changelist")},
                ],
            },
            {
                "title": _("Доступ"),
                "items": [
                    {"title": _("Користувачі"), "icon": "person", "link": reverse_lazy("admin:auth_user_changelist")},
                ],
            },
        ],
    },
}
