from django.apps import AppConfig


class SalesChannelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sales_channels'

    def ready(self):
        from . import receivers
