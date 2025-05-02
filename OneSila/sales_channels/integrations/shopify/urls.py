# integrations/shopify/urls.py

from django.urls import path
from . import views

app_name = "shopify"

urlpatterns = [
    path("oauth/start", views.shopify_auth_start, name="shopify_oauth_start"),
    path("oauth/callback", views.shopify_auth_callback, name="shopify_oauth_callback"),
]
