"""
URL configuration for OneSila project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.urls import include, path
from strawberry.django.views import AsyncGraphQLView
from .schema import schema
from django.conf.urls.static import static

urlpatterns = [
    path('', include('core.urls')),
    path(f'admin{settings.ADMIN_ROUTE_SUFFIX}/', admin.site.urls),
    path('contacts/', include('contacts.urls')),
    path('currencies/', include('currencies.urls')),
    path('customs/', include('customs.urls')),
    path('eancodes/', include('eancodes.urls')),
    path('inventory/', include('inventory.urls')),
    path('media/', include('media.urls')),
    path('sales/', include('orders.urls')),
    path('products/', include('products.urls')),
    path('properties/', include('properties.urls')),
    path('sales-prices/', include('sales_prices.urls')),
    path('taxes/', include('taxes.urls')),
    path('units/', include('units.urls')),
    path('sales_channels/', include('sales_channels.urls')),
    path('integrations/shopify/', include('sales_channels.integrations.shopify.urls')),
    path('integrations', include('integrations.urls')),
    path('graphql/',
        AsyncGraphQLView.as_view(
            schema=schema,
            graphiql=settings.DEBUG,
            multipart_uploads_enabled=True
        ),
        name='graphql',
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
