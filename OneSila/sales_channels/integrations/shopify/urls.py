# integrations/shopify/urls.py

from django.urls import path
from . import views
from .views import ShopifyInstalledView

app_name = "shopify"

urlpatterns = [
    path("customerdata/request/", views.shopify_customer_data_request, name="shopify_customer_data_request"),
    path("customerdata/erase/", views.shopify_customer_redact, name="shopify_customer_data_erase"),
    path("shopdata/erase/", views.shopify_shop_redact, name="shopify_shop_data_erase"),
]
