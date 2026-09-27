from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

admin.site.site_header = "Premier Parts"
admin.site.site_title = "Premier Parts"
admin.site.index_title = "Дашборд"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.core.urls")),
    path("api/", include("apps.catalog.urls")),
    path("api/", include("apps.content.urls")),
    path("api/", include("apps.search.urls")),
    path("api/", include("apps.vin.urls")),
    path("api/", include("apps.orders.urls")),
    path("api/", include("apps.accounts.urls")),
]

if settings.SERVE_MEDIA:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
