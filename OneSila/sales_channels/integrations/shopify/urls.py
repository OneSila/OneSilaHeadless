# integrations/shopify/urls.py

from django.urls import path
from . import views

app_name = "shopify"

urlpatterns = [
    path("oauth/start", views.shopify_auth_start, name="shopify_oauth_start"),
    path("oauth/callback", views.shopify_auth_callback, name="shopify_oauth_callback"),

    path("customerdata/request/", views.shopify_customer_data_request, name="shopify_customer_data_request"),
    path("customerdata/erase/", views.shopify_customer_redact, name="shopify_customer_data_erase"),
    path("shopdata/erase/", views.shopify_shop_redact, name="shopify_shop_data_erase"),
]
