from django.urls import path, include
from . import views
from .views import IntegrationListView, ShopifyIntegrationDetailView

app_name = 'integrations'

urlpatterns = [
    path("", IntegrationListView.as_view(), name="integrations_list"),
    path("shopify/<str:id>/", ShopifyIntegrationDetailView.as_view(), name="shopify_integration_detail"),

]

