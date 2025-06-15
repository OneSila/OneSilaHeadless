from sales_channels.factories.products.eancodes import RemoteEanCodeUpdateFactory
from sales_channels.integrations.woocommerce.models import WoocommerceEanCode
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.factories.mixins import WoocommerceProductTypeMixin
from sales_channels.integrations.woocommerce.constants import EAN_CODE_WOOCOMMERCE_FIELD_NAME

from .mixins import SerialiserMixin
from .properties import WooCommerceProductAttributeMixin

import logging
logger = logging.getLogger(__name__)


class WooCommerceEanCodeUpdateFactory(WooCommerceProductAttributeMixin, GetWoocommerceAPIMixin, RemoteEanCodeUpdateFactory, WoocommerceProductTypeMixin):
    # Eans are not stored remotely per se.
    # they are part of the product attribute payload as an option
    remote_model_class = WoocommerceEanCode

    def customize_payload(self):
        product = self.get_local_product()
        ean_code = product.eancode_set.last()

        try:
            self.payload[EAN_CODE_WOOCOMMERCE_FIELD_NAME] = ean_code.ean_code
        except AttributeError:
            # No EanCode, send empty payload
            self.payload[EAN_CODE_WOOCOMMERCE_FIELD_NAME] = ''

        return self.payload

    def update_remote(self):
        if self.is_woocommerce_variant_product:
            parent_id = self.remote_product.remote_parent_product.remote_id
            variant_id = self.remote_product.remote_id
            return self.api.update_product_variation(parent_id, variant_id, **self.payload)
        else:
            product_id = self.remote_product.remote_id
            return self.api.update_product(product_id, **self.payload)
