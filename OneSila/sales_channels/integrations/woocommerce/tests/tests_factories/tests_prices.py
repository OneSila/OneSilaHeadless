from sales_prices.models import SalesPrice
from sales_channels.integrations.woocommerce.models import WoocommerceProduct
from .tests_products import WooCommerceProductFactoryTestMixin
from sales_channels.integrations.woocommerce.factories.prices import WoocommercePriceUpdateFactory

import logging
logger = logging.getLogger(__name__)


class WooCommercePriceUpdateFactoryTest(WooCommerceProductFactoryTestMixin):
    def test_woocom_price_update_for_simple_product(self):
        product = self.create_test_product(
            sku="tshirt-simple-product",
            name="Test Product",
            assign_to_sales_channel=True,
            rule=self.product_rule
        )

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

        self.assertEqual(float(resp_product['regular_price']), price.rrp)
        self.assertEqual(float(resp_product['sale_price']), price.price)

        price.rrp = 291291
        price.price = 81212
        price.save()

        # Update remote product instance and run it
        factory = WoocommercePriceUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_product=remote_product,
            currency=currency,
        )
        factory.run()

        self.assertTrue(factory.preflight_check())

        # Verify the remote property was updated in database
        resp_product = self.api.get_product(remote_product.remote_id)

        self.assertEqual(float(resp_product['regular_price']), price.rrp)
        self.assertEqual(float(resp_product['sale_price']), price.price)
