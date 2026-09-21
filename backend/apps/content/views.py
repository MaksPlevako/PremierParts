from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.catalog.services.pricing import live_promotions
from apps.catalog.services.queries import card_queryset, product_cards
from apps.catalog.views import promotion_products_q

from .models import Banner, Page, Promotion, SiteSettings
from .serializers import banner_data, page_data, promotion_data, settings_data


@api_view(["GET"])
def site_settings(request):
    return Response(settings_data(SiteSettings.load()))


@api_view(["GET"])
def banners(request):
    qs = Banner.objects.live()
    if placement := request.query_params.get("placement"):
        qs = qs.filter(placement=placement)
    return Response([banner_data(b) for b in qs])


@api_view(["GET"])
def promotions(request):
    return Response([promotion_data(p) for p in Promotion.objects.live()])


@api_view(["GET"])
def promotion_detail(request, slug):
    promo = get_object_or_404(Promotion.objects.live(), slug=slug)
    products = card_queryset().filter(promotion_products_q(promo)).distinct().order_by("-popularity")[:48]
    data = promotion_data(promo)
    data["products"] = product_cards(products, live_promotions())
    return Response(data)


@api_view(["GET"])
def pages(request):
    return Response([page_data(p, with_body=False) for p in Page.objects.filter(is_active=True)])


@api_view(["GET"])
def page_detail(request, slug):
    return Response(page_data(get_object_or_404(Page, slug=slug, is_active=True)))
