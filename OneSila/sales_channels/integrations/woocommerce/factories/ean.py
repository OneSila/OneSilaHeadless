from sales_channels.factories.products.eancodes import RemoteEanCodeUpdateFactory
from sales_channels.integrations.woocommerce.models import WoocommerceEanCode
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin

from .mixins import SerialiserMixin


class WooCommerceEanCodeUpdateFactory(GetWoocommerceAPIMixin, SerialiserMixin, RemoteEanCodeUpdateFactory):
    # Eans are not stored remotely per se.
    # they are part of the product attribute payload as an option
    remote_model_class = WoocommerceEanCode
