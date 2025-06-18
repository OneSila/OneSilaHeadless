from sales_channels.factories.products.eancodes import RemoteEanCodeUpdateFactory
from sales_channels.integrations.woocommerce.models import WoocommerceEanCode
from .mixins import WooCommercePayloadMixin, WooCommerceUpdateRemoteProductMixin

import logging
logger = logging.getLogger(__name__)


class WooCommerceEanCodeUpdateFactory(WooCommerceUpdateRemoteProductMixin, WooCommercePayloadMixin,
        RemoteEanCodeUpdateFactory):
    # Eans are not stored remotely per se.
    # they are part of the product attribute payload as an option
    remote_model_class = WoocommerceEanCode

    def update_remote(self):
        return self.update_remote_product()

    # def update_remote(self):
    #     if self.is_woocommerce_variant_product:
    #         parent_id = self.remote_product.remote_parent_product.remote_id
    #         variant_id = self.remote_product.remote_id
    #         return self.api.update_product_variation(parent_id, variant_id, **self.payload)
    #     else:
    #         product_id = self.remote_product.remote_id
    #         return self.api.update_product(product_id, **self.payload)
