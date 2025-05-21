import json
from sales_channels.factories.prices.prices import RemotePriceUpdateFactory
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommercePrice

import logging
logger = logging.getLogger(__name__)


class WoocommercePriceUpdateFactory(GetWoocommerceAPIMixin, RemotePriceUpdateFactory):
    remote_model_class = WoocommercePrice
    # create_factory_class =
    fields_map = {
        'price': 'regular_price',
        'discount_price': 'sale_price',
    }

    def preflight_check(self):
        return True

    def update_remote(self):
        currency_code = self.to_update_currencies[0]
        price_info = self.price_data.get(currency_code, {})

        logger.debug('--------------------------------')
        logger.debug('--------------------------------')
        logger.debug('--------------------------------')
        logger.debug(f"Currency code: {currency_code}")
        logger.debug(f"price_info: {price_info}")
        logger.debug('--------------------------------')
        logger.debug('--------------------------------')
        logger.debug('--------------------------------')

        if not price_info:
            raise ValueError(f"No price data for currency: {currency_code}")

        if self.is_woocommerce_simple_product:
            self.api.update_product(self.remote_product.remote_id, **self.payload)
        elif self.is_woocommerce_variant_product:
            self.api.update_variant(self.remote_product.remote_parent_id, self.remote_product.remote_id, **self.payload)
        elif self.is_woocommerce_configurable_product:
            raise NotImplementedError("Configurable products are not supported for price-updates.")
        else:
            raise NotImplementedError("Invalid product type")

    def run(self):
        if not self.preflight_check():
            return

        self.set_api()
        self.preflight_process()

        # Handle instance creation logic after preflight processes
        self.handle_remote_instance_creation()

        # Abort if the instance was created / re-created
        if not self.successfully_updated:
            return

        self.build_payload()
        self.customize_payload()
        if self.needs_update() and self.additional_update_check():
            self.update()
