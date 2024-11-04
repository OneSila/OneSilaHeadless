from django.apps import AppConfig


class QuickbooksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounting.integrations.quickbooks'
    label = 'quickbooks'

    def ready(self):
        from . import receivers