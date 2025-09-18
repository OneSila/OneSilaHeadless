from django.apps import AppConfig


class WoocommerceConfig(AppConfig):
    name = 'sales_channels.integrations.woocommerce'
    default_auto_field = 'django.db.models.BigAutoField'
    verbose_name = 'Woocommerce Integration'
    label = 'woocommerce'

    def ready(self):
        from . import receivers
