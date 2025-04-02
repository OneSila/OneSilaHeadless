from django.apps import AppConfig


class ImportsExportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'imports_exports'
def ready(self):
        from . import receivers