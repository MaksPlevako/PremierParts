from django.urls import path

from . import views

urlpatterns = [
    path("home", views.home),
    path("categories", views.categories),
    path("seo/sitemap-index", views.sitemap_index),
    path("categories/<slug:slug>", views.category_detail),
    path("products/<slug:slug>", views.product_detail),
    path("makes", views.makes),
    path("makes/<slug:slug>", views.make_detail),
    path("generations/<int:pk>", views.generation_detail),
    path("cars/<slug:make_slug>/<slug:model_slug>", views.model_detail),
    path("cars/<slug:make_slug>/<slug:model_slug>/<slug:gen_slug>", views.car_detail),
    path("legacy/resolve", views.legacy_resolve),
]
