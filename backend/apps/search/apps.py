from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.search"
    verbose_name = "Пошук"
    label = "search"

    def ready(self):
        from . import signals  # noqa: F401
