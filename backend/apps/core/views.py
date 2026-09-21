from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response


def _db_ok() -> bool:
    try:
        connection.ensure_connection()
        return True
    except Exception:
        return False


def _search_ok() -> bool:
    try:
        from apps.search.index import client

        return client().is_healthy()
    except Exception:
        return False


@api_view(["GET"])
def health(request):
    return Response({"status": "ok", "db": _db_ok(), "search": _search_ok()})
