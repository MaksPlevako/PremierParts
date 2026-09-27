from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.catalog.services.pricing import live_promotions
from apps.catalog.services.queries import card_queryset, product_cards

from . import novaposhta
from .models import Order
from .serializers import OrderCreateSerializer, QuickOrderSerializer, order_summary
from .services import OrderInput, create_order, create_quick_order


@api_view(["POST"])
def orders_create(request):
    ser = OrderCreateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = dict(ser.validated_data)
    items = [dict(i) for i in data.pop("items")]
    user = request.user if request.user and request.user.is_authenticated else None
    order = create_order(OrderInput(items=items, user=user, **data))
    return Response(
        {"number": order.number, "access_token": str(order.access_token), "total": float(order.total)},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
def orders_quick(request):
    ser = QuickOrderSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    user = request.user if request.user and request.user.is_authenticated else None
    order = create_quick_order(**ser.validated_data, user=user)
    return Response(
        {"number": order.number, "access_token": str(order.access_token), "total": float(order.total)},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def order_detail(request, number):
    token = request.query_params.get("token") or ""
    order = get_object_or_404(Order, number=number)
    if str(order.access_token) != token:
        return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(order_summary(order))


@api_view(["POST"])
def cart_validate(request):
    items = request.data.get("items") or []
    wanted = {}
    for item in items[:100]:
        try:
            wanted[int(item["product_id"])] = max(1, min(int(item.get("qty") or 1), 99))
        except (KeyError, TypeError, ValueError):
            continue
    cards = {c["id"]: c for c in product_cards(card_queryset().filter(id__in=wanted), live_promotions())}
    result, total = [], 0.0
    for product_id, qty in wanted.items():
        card = cards.get(product_id)
        result.append({"product_id": product_id, "qty": qty, "available": card is not None, "card": card})
        if card:
            unit = card["sale_price"] if card["sale_price"] is not None else card["price"]
            total += unit * qty
    return Response({"items": result, "total": total})


@api_view(["GET"])
def np_cities(request):
    if not novaposhta.enabled():
        return Response({"enabled": False, "results": []})
    q = (request.query_params.get("q") or "").strip()
    if len(q) < 2:
        return Response({"enabled": True, "results": []})
    try:
        return Response({"enabled": True, "results": novaposhta.cities(q)})
    except Exception:
        return Response({"enabled": False, "results": []})


@api_view(["GET"])
def np_warehouses(request):
    if not novaposhta.enabled():
        return Response({"enabled": False, "results": []})
    city_ref = request.query_params.get("city_ref") or ""
    try:
        return Response({"enabled": True, "results": novaposhta.warehouses(city_ref, request.query_params.get("q") or "")})
    except Exception:
        return Response({"enabled": False, "results": []})
