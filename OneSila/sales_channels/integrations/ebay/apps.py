from django.apps import AppConfig


class EbayConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sales_channels.integrations.ebay'
    label = 'ebay'

    def ready(self):
        from . import receivers
