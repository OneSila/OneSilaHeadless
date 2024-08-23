from django.apps import AppConfig


class OrderReturnsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'order_returns'


def ready(self):
    from . import receivers
