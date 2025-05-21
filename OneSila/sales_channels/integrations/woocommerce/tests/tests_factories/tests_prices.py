

from .mixins import TestCaseWoocommerceMixin
from django.conf import settings
from django.db import transaction

from sales_channels.integrations.woocommerce.tests.helpers import CreateTestProductMixin
from media.tests.helpers import CreateImageMixin
from properties.models import Property, ProductPropertiesRule, ProductProperty, \
    ProductPropertiesRuleItem
from products.models import ConfigurableVariation
from sales_prices.models import SalesPrice
from sales_channels.integrations.woocommerce.models import WoocommerceProduct
from .tests_products import WooCommerceProductFactoryTestMixin
from sales_channels.integrations.woocommerce.factories.products import (
    WooCommerceProductCreateFactory,
    WooCommerceProductUpdateFactory
)
from sales_channels.integrations.woocommerce.factories.prices import WoocommercePriceUpdateFactory
from sales_channels.integrations.woocommerce.factories.properties import WooCommerceGlobalAttributeCreateFactory

import logging
logger = logging.getLogger(__name__)


class WooCommercePriceUpdateFactoryTest(WooCommerceProductFactoryTestMixin):

    def test_woocom_simple_product_price_update(self):
        product = self.create_test_product(
            sku="tshirt-simple-product",
            name="Test Product",
            assign_to_sales_channel=True,
            rule=self.product_rule
        )

        # Push the product remotely.
        factory = WooCommerceProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product
        )
        factory.run()

        self.assertEqual(factory.payload['sku'], product.sku)

        remote_product = WoocommerceProduct.objects.get(
            sales_channel=self.sales_channel,
            local_instance=product
        )
        self.assertIsNotNone(remote_product.remote_id)

        # Verify it exists in WooCommerce
        resp_product = self.api.get_product(remote_product.remote_id)
        self.assertIsNotNone(resp_product)

        self.assertEqual(resp_product['name'], product.name)
        self.assertEqual(resp_product['sku'], product.sku)
        self.assertEqual(resp_product['type'], 'simple')

        # Get the price object for the product in the sales channel's currency
        logger.debug(f"All remote currencies: {self.sales_channel.remotecurrency_set.all().values('local_instance__iso_code')}")
        currency = self.sales_channel.remotecurrency_set.first().local_instance
        logger.debug(f"Currency selected: {currency}")
        price = SalesPrice.objects.get(
            product=product,
            currency=currency
        )

        price.rrp = 291291
        price.price = 81212
        price.save()

        # Update remote product instance and run it
        factory = WoocommercePriceUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=price,
            remote_product=remote_product,
            currency=currency,
            skip_checks=True
        )
        factory.run()

        # Verify the remote property was updated in database
        resp_product = self.api.get_product(remote_product.remote_id)

        self.assertEqual(float(resp_product['price']), price.rrp)
        self.assertEqual(float(resp_product['sale_price']), price.price)

        input("Press Enter to continue...")
