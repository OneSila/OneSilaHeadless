from django.apps import AppConfig


class ShopifyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sales_channels.integrations.shopify'
    label = 'shopify'

    def ready(self):
        from . import receivers
