from django.apps import AppConfig


class Magento2Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sales_channels.integrations.magento2'
    label = 'magento2'

    def ready(self):
            from . import receivers