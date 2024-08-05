from django.apps import AppConfig
import django.db.models.options as options


options.DEFAULT_NAMES = (*options.DEFAULT_NAMES, 'backorder_item_count',)


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'

    def ready(self):
        from . import receivers
