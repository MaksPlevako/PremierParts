from django.urls import path

from . import views

urlpatterns = [
    path("vin/decode", views.vin_decode),
    path("vin/requests", views.vin_request),
]
