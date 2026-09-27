import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class Order(models.Model):
    class Kind(models.TextChoices):
        REGULAR = "regular", _("Звичайне")
        QUICK = "quick", _("В 1 клік")

    class Status(models.TextChoices):
        NEW = "new", _("Нове")
        CONFIRMED = "confirmed", _("Підтверджене")
        SHIPPED = "shipped", _("Відправлене")
        COMPLETED = "completed", _("Виконане")
        CANCELED = "canceled", _("Скасоване")

    class Delivery(models.TextChoices):
        NP_BRANCH = "np_branch", _("Нова Пошта — відділення")
        NP_COURIER = "np_courier", _("Нова Пошта — кур'єр")
        PICKUP = "pickup", _("Самовивіз (Київ)")
        TAXI = "taxi", _("Таксі по Києву")

    class Payment(models.TextChoices):
        IBAN = "iban", _("Оплата на рахунок ФОП")
        CARD_PICKUP = "card_pickup", _("Карткою при самовивозі")
        CASH_PICKUP = "cash_pickup", _("Готівкою при самовивозі")

    number = models.CharField(_("номер"), max_length=20, unique=True, blank=True)
    access_token = models.UUIDField(default=uuid.uuid4, editable=False)
    kind = models.CharField(_("тип"), max_length=10, choices=Kind.choices, default=Kind.REGULAR)
    status = models.CharField(_("статус"), max_length=12, choices=Status.choices, default=Status.NEW)
    customer_name = models.CharField(_("ім'я"), max_length=160, blank=True)
    phone = models.CharField(_("телефон"), max_length=20)
    email = models.EmailField(_("email"), blank=True)
    delivery_method = models.CharField(_("доставка"), max_length=12, choices=Delivery.choices, default=Delivery.NP_BRANCH)
    city = models.CharField(_("місто"), max_length=160, blank=True)
    np_branch = models.CharField(_("відділення НП"), max_length=255, blank=True)
    address = models.CharField(_("адреса"), max_length=255, blank=True)
    tracking_number = models.CharField(_("номер ТТН"), max_length=80, blank=True)
    payment_method = models.CharField(_("оплата"), max_length=12, choices=Payment.choices, default=Payment.IBAN)
    comment = models.TextField(_("коментар клієнта"), blank=True)
    car_snapshot = models.JSONField(_("авто клієнта"), default=dict, blank=True)
    subtotal = models.DecimalField(_("сума без знижки"), max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(_("знижка"), max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(_("до сплати"), max_digits=12, decimal_places=2, default=0)
    manager_note = models.TextField(_("нотатка менеджера"), blank=True)
    user = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    created_at = models.DateTimeField(_("створено"), auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("замовлення")
        verbose_name_plural = _("замовлення")

    def __str__(self):
        return self.number or f"#{self.pk}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.number:
            self.number = f"PP-{self.pk:06d}"
            super().save(update_fields=["number"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(_("назва"), max_length=300)
    sku = models.CharField(_("артикул"), max_length=80, blank=True)
    price = models.DecimalField(_("ціна"), max_digits=10, decimal_places=2)
    old_price = models.DecimalField(_("ціна без знижки"), max_digits=10, decimal_places=2, null=True, blank=True)
    qty = models.PositiveIntegerField(_("кількість"), default=1)
    line_total = models.DecimalField(_("сума"), max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = _("позиція")
        verbose_name_plural = _("позиції")

    def __str__(self):
        return f"{self.name} × {self.qty}"
