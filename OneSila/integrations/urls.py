from django.urls import path, include

from sales_channels.integrations.shopify.views import ShopifyInstalledView, ShopifyEntryView
from sales_channels.integrations.amazon.views import AmazonInstalledView, AmazonEntryView
from . import views
from .views import IntegrationListView, ShopifyIntegrationDetailView, AmazonIntegrationDetailView

app_name = 'integrations'

urlpatterns = [
    path("", IntegrationListView.as_view(), name="integrations_list"),
    path("shopify/<str:id>/", ShopifyIntegrationDetailView.as_view(), name="shopify_integration_detail"),
    path("shopify/installed", ShopifyInstalledView.as_view(), name="shopify_oauth_callback"),
    path("shopify/entry", ShopifyEntryView.as_view(), name="shopify_oauth_entry"),
    path("amazon/<str:id>/", AmazonIntegrationDetailView.as_view(), name="amazon_integration_detail"),
    path("amazon/installed", AmazonInstalledView.as_view(), name="amazon_oauth_callback"),
    path("amazon/entry", AmazonEntryView.as_view(), name="amazon_oauth_entry"),

]
