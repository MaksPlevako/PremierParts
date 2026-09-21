from rest_framework.decorators import api_view
from rest_framework.response import Response

from .service import ListingParams, query_products, suggest


@api_view(["GET"])
def products(request):
    return Response(query_products(ListingParams.from_query(request.query_params)))


@api_view(["GET"])
def search(request):
    return Response(query_products(ListingParams.from_query(request.query_params)))


@api_view(["GET"])
def search_suggest(request):
    q = (request.query_params.get("q") or "").strip()[:200]
    try:
        car = int(request.query_params.get("car") or 0) or None
    except ValueError:
        car = None
    return Response(suggest(q, car))
