from django.conf import settings
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.core.normalize import normalize_phone

from .decoder import VinError, validate_vin
from .models import VinRequest
from .service import decode_and_match


@api_view(["POST"])
def vin_decode(request):
    try:
        return Response(decode_and_match(str(request.data.get("vin", ""))))
    except VinError as exc:
        return Response({"valid": False, "error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class VinRequestSerializer(serializers.Serializer):
    vin = serializers.CharField(max_length=40)
    name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=40)
    part_query = serializers.CharField(max_length=500, required=False, allow_blank=True)
    comment = serializers.CharField(max_length=2000, required=False, allow_blank=True)

    def validate_vin(self, value):
        try:
            vin, _warnings = validate_vin(value)
        except VinError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return vin

    def validate_phone(self, value):
        phone = normalize_phone(value)
        if not phone:
            raise serializers.ValidationError("Вкажіть номер у форматі +380XXXXXXXXX")
        return phone


@api_view(["POST"])
def vin_request(request):
    ser = VinRequestSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data
    try:
        decoded = decode_and_match(data["vin"])
    except Exception:
        decoded = {}
    req = VinRequest.objects.create(decoded=decoded, **data)

    from apps.orders.notify import notify_manager

    car = decoded.get("matches", [{}])[0].get("full_label") if decoded.get("matches") else None
    notify_manager(
        f"Новий запит за VIN {req.vin}",
        [
            f"Клієнт: {req.name or '—'} {req.phone}",
            f"Деталь: {req.part_query or '—'}",
            f"Авто: {car or ' '.join(filter(None, [decoded.get('make'), decoded.get('model'), str(decoded.get('year') or '')])) or '—'}",
            f"Коментар: {req.comment or '—'}",
        ],
        context={
            "summary": "Клієнт надіслав запит на підбір запчастини за VIN.",
            "action_url": f"{settings.SITE_URL}/admin/vin/vinrequest/{req.pk}/change/",
            "action_label": "Відкрити VIN-запит",
        },
    )
    return Response({"id": req.id}, status=status.HTTP_201_CREATED)
