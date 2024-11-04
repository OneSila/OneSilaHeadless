from django.apps import AppConfig
import django.db.models.options as options
options.DEFAULT_NAMES = (*options.DEFAULT_NAMES, 'user_exceptions',)


class IntegrationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'integrations'

def ready(self):
        from . import receivers