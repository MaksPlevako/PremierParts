from django.db import models
from django.utils.translation import gettext_lazy as _


class Wmi(models.Model):
    """World Manufacturer Identifier: first 3 VIN characters -> make and country."""

    code = models.CharField(_("код"), max_length=3, unique=True)
    make_name = models.CharField(_("марка"), max_length=80)
    country = models.CharField(_("країна"), max_length=80, blank=True)

    class Meta:
        ordering = ["code"]
        verbose_name = _("код виробника (WMI)")
        verbose_name_plural = _("коди виробників (WMI)")

    def __str__(self):
        return f"{self.code} — {self.make_name}"


class VinDecodeCache(models.Model):
    vin = models.CharField(max_length=17, unique=True)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("кеш розшифровки VIN")
        verbose_name_plural = _("кеш розшифровки VIN")


class VinRequest(models.Model):
    class Status(models.TextChoices):
        NEW = "new", _("Новий")
        IN_PROGRESS = "in_progress", _("В роботі")
        DONE = "done", _("Опрацьовано")

    vin = models.CharField("VIN", max_length=17)
    name = models.CharField(_("ім'я"), max_length=120, blank=True)
    phone = models.CharField(_("телефон"), max_length=20)
    part_query = models.CharField(_("яка деталь потрібна"), max_length=500, blank=True)
    comment = models.TextField(_("коментар"), blank=True)
    decoded = models.JSONField(_("розшифровка"), default=dict, blank=True)
    status = models.CharField(_("статус"), max_length=16, choices=Status.choices, default=Status.NEW)
    manager_note = models.TextField(_("нотатка менеджера"), blank=True)
    created_at = models.DateTimeField(_("створено"), auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("запит за VIN")
        verbose_name_plural = _("запити за VIN")

    def __str__(self):
        return f"{self.vin} · {self.phone}"
