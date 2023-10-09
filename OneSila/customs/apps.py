from django.apps import AppConfig


class CustomsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'customs'

    def ready(self):
        from . import receivers
