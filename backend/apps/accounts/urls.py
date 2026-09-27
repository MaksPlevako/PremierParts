from django.urls import path

from . import oauth, views

urlpatterns = [
    path("account/config", views.auth_config),
    path("account/register", views.register),
    path("account/verify-email", views.verify_email),
    path("account/resend-email", views.resend_email),
    path("account/login", views.sign_in),
    path("account/logout", views.sign_out),
    path("account/password/reset", views.request_reset),
    path("account/password/confirm", views.confirm_reset),
    path("account/profile", views.profile),
    path("account/garage", views.garage),
    path("account/garage/<int:pk>", views.garage_item),
    path("account/orders", views.my_orders),
    path("account/orders/<str:number>", views.my_order),
    path("account/recommendations", views.recommendations),
    path("account/oauth/<str:provider>/start", oauth.start),
    path("account/oauth/<str:provider>/callback", oauth.callback),
]
