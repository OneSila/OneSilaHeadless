from sales_channels.factories.products.eancodes import RemoteEanCodeUpdateFactory
from sales_channels.integrations.woocommerce.models import WoocommerceEanCode
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.factories.mixins import WoocommerceProductTypeMixin

from .mixins import SerialiserMixin
from .properties import WooCommerceProductAttributeMixin

import logging
logger = logging.getLogger(__name__)


class WooCommerceEanCodeUpdateFactory(WooCommerceProductAttributeMixin, GetWoocommerceAPIMixin, RemoteEanCodeUpdateFactory):
    # Eans are not stored remotely per se.
    # they are part of the product attribute payload as an option
    remote_model_class = WoocommerceEanCode

    def customize_payload(self):
        product = self.get_local_product()
        ean_code = product.eancode_set.last()

        try:
            self.payload['global_unique_id'] = ean_code.ean_code
        except AttributeError:
            # No EanCode, send empty payload
            self.payload['global_unique_id'] = ''

        return self.payload

    def update_remote(self):
        if self.is_woocommerce_variant_product:
            logger.info(f"Updating variant {self.remote_product.remote_id} with payload {self.payload}")
            return self.api.update_variant(self.remote_product.remote_parent_id, self.remote_product.remote_id, **self.payload)
        elif self.is_woocommerce_simple_product or self.is_woocommerce_configurable_product:
            logger.info(f"Updating product {self.remote_product.remote_id} with payload {self.payload}")
            return self.api.update_product(self.remote_product.remote_id, **self.payload)
        else:
            raise NotImplementedError("Invalid product type")
