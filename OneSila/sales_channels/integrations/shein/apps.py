from django.apps import AppConfig


class SheinConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shein'

    def ready(self):
        from . import receivers