from django.apps import AppConfig


class AmazonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    label = 'amazon'
    name = 'sales_channels.integrations.amazon'

    def ready(self):
        from . import receivers