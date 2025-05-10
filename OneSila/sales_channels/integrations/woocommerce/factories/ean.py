from sales_channels.factories.products.eancodes import RemoteEanCodeUpdateFactory
from sales_channels.integrations.woocommerce.models import WoocommerceEanCode
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin

from .mixins import SerialiserMixin
from .properties import WooCommerceProductAttributeMixin


class WooCommerceEanCodeUpdateFactory(WooCommerceProductAttributeMixin, GetWoocommerceAPIMixin, RemoteEanCodeUpdateFactory):
    # Eans are not stored remotely per se.
    # they are part of the product attribute payload as an option
    remote_model_class = WoocommerceEanCode

    def customize_payload(self):
        return self.apply_attribute_payload()

    def update_remote(self):
        return self.api.update_product(self.remote_product.remote_id, **self.payload)
