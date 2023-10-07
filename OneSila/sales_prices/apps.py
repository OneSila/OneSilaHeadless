from django.apps import AppConfig


class SalesPricesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sales_prices'

    def ready(self):
        from . import receivers
