from django.urls import path, include

from sales_channels.integrations.shopify.views import ShopifyInstalledView, ShopifyEntryView
from . import views
from .views import IntegrationListView, ShopifyIntegrationDetailView

app_name = 'integrations'

urlpatterns = [
    path("", IntegrationListView.as_view(), name="integrations_list"),
    path("shopify/<str:id>/", ShopifyIntegrationDetailView.as_view(), name="shopify_integration_detail"),
    path("shopify/installed", ShopifyInstalledView.as_view(), name="shopify_oauth_callback"),
    path("shopify/entry", ShopifyEntryView.as_view(), name="shopify_oauth_entry"),

]
