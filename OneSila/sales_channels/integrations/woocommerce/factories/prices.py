import json
from sales_channels.factories.prices.prices import RemotePriceUpdateFactory
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommercePrice
from .mixins import SerialiserMixin, WoocommerceProductTypeMixin
import logging
logger = logging.getLogger(__name__)


class WoocommercePriceUpdateFactory(SerialiserMixin, GetWoocommerceAPIMixin, WoocommerceProductTypeMixin, RemotePriceUpdateFactory):
    remote_model_class = WoocommercePrice

    def customize_payload(self):
        currency_code = self.to_update_currencies[0]
        price_info = self.price_data.get(currency_code, {})

        self.payload['regular_price'] = price_info.get('price', None)
        self.payload['sale_price'] = price_info.get('discount_price', None)
        return self.payload

    def update_remote(self):
        if self.is_woocommerce_simple_product:
            return self.api.update_product(self.remote_product.remote_id, **self.payload)
        elif self.is_woocommerce_variant_product:
            return self.api.update_variant(self.remote_product.remote_parent_id, self.remote_product.remote_id, **self.payload)
        elif self.is_woocommerce_configurable_product:
            raise NotImplementedError("Configurable products are not supported for price-updates.")
        else:
            raise NotImplementedError("Invalid product type")
