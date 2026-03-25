from django.apps import AppConfig


class MiraklConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sales_channels.integrations.mirakl'
    label = 'mirakl'

    def ready(self):
        from . import receivers
