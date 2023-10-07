from django.apps import AppConfig


class EancodesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'eancodes'

    def ready(self):
        from . import receivers
