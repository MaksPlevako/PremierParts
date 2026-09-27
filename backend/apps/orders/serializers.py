from rest_framework import serializers

from apps.core.normalize import normalize_phone

from .models import Order


def _phone(value: str) -> str:
    phone = normalize_phone(value)
    if not phone:
        raise serializers.ValidationError("Вкажіть номер у форматі +380XXXXXXXXX")
    return phone


class OrderItemInput(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    qty = serializers.IntegerField(min_value=1, max_value=99, default=1)


class OrderCreateSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=160)
    phone = serializers.CharField(max_length=40)
    email = serializers.EmailField(required=False, allow_blank=True)
    delivery_method = serializers.ChoiceField(choices=Order.Delivery.choices)
    city = serializers.CharField(max_length=160, required=False, allow_blank=True)
    np_branch = serializers.CharField(max_length=255, required=False, allow_blank=True)
    address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(choices=Order.Payment.choices)
    comment = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    car_generation_id = serializers.IntegerField(required=False, allow_null=True)
    items = OrderItemInput(many=True)

    def validate_phone(self, value):
        return _phone(value)

    def validate(self, attrs):
        method = attrs["delivery_method"]
        errors = {}
        if method in (Order.Delivery.NP_BRANCH, Order.Delivery.NP_COURIER) and not attrs.get("city"):
            errors["city"] = ["Вкажіть місто"]
        if method == Order.Delivery.NP_BRANCH and not attrs.get("np_branch"):
            errors["np_branch"] = ["Вкажіть відділення Нової Пошти"]
        if method in (Order.Delivery.NP_COURIER, Order.Delivery.TAXI) and not attrs.get("address"):
            errors["address"] = ["Вкажіть адресу доставки"]
        if method not in (Order.Delivery.PICKUP,) and attrs["payment_method"] != Order.Payment.IBAN:
            errors["payment_method"] = ["Оплата карткою чи готівкою доступна лише при самовивозі"]
        if not attrs.get("items"):
            errors["items"] = ["Кошик порожній"]
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class QuickOrderSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=40)
    name = serializers.CharField(max_length=160, required=False, allow_blank=True)
    product_id = serializers.IntegerField(min_value=1)
    qty = serializers.IntegerField(min_value=1, max_value=99, default=1)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)
    car_generation_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_phone(self, value):
        return _phone(value)


def order_summary(order: Order) -> dict:
    return {
        "number": order.number,
        "kind": order.kind,
        "status": order.status,
        "status_label": order.get_status_display(),
        "customer_name": order.customer_name,
        "phone": order.phone,
        "email": order.email,
        "delivery_method": order.delivery_method,
        "delivery_label": order.get_delivery_method_display(),
        "city": order.city,
        "np_branch": order.np_branch,
        "address": order.address,
        "tracking_number": order.tracking_number,
        "payment_method": order.payment_method,
        "payment_label": order.get_payment_method_display(),
        "comment": order.comment,
        "car": order.car_snapshot or None,
        "subtotal": float(order.subtotal),
        "discount": float(order.discount),
        "total": float(order.total),
        "created_at": order.created_at.isoformat(),
        "items": [
            {
                "product_id": i.product_id,
                "slug": i.product.slug if i.product else None,
                "name": i.name,
                "sku": i.sku,
                "price": float(i.price),
                "old_price": float(i.old_price) if i.old_price else None,
                "qty": i.qty,
                "line_total": float(i.line_total),
            }
            for i in order.items.select_related("product")
        ],
    }
