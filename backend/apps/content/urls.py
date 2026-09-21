from django.urls import path

from . import views

urlpatterns = [
    path("settings", views.site_settings),
    path("banners", views.banners),
    path("promotions", views.promotions),
    path("promotions/<slug:slug>", views.promotion_detail),
    path("pages", views.pages),
    path("pages/<slug:slug>", views.page_detail),
]
