from django.urls import path

from . import views

urlpatterns = [
    path("products", views.products),
    path("search", views.search),
    path("search/suggest", views.search_suggest),
]
