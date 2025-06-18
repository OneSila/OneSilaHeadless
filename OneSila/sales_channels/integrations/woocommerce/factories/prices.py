import json
from sales_channels.factories.prices.prices import RemotePriceUpdateFactory
from sales_channels.integrations.woocommerce.models import WoocommercePrice
from .mixins import WooCommercePayloadMixin, WooCommerceUpdateRemoteProductMixin
import logging
logger = logging.getLogger(__name__)


class WoocommercePriceUpdateFactory(WooCommerceUpdateRemoteProductMixin, WooCommercePayloadMixin, RemotePriceUpdateFactory):
    remote_model_class = WoocommercePrice

    def update_remote(self):
        if self.is_woocommerce_configurable_product:
            raise NotImplementedError("Configurable products are not supported for price-updates.")

        return self.update_remote_product()
