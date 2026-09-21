from django.urls import path

from . import views

urlpatterns = [
    path("orders", views.orders_create),
    path("orders/quick", views.orders_quick),
    path("orders/<str:number>", views.order_detail),
    path("cart/validate", views.cart_validate),
    path("np/cities", views.np_cities),
    path("np/warehouses", views.np_warehouses),
]
