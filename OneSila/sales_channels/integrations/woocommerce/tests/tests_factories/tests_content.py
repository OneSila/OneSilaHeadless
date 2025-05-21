from .tests_products import WooCommerceProductFactoryTestMixin
from sales_channels.integrations.woocommerce.factories.products import (
    WooCommerceProductCreateFactory,
)
from sales_channels.integrations.woocommerce.factories.content import WoocommerceProductContentUpdateFactory


import logging
logger = logging.getLogger(__name__)


class WooCommercePriceUpdateFactoryTest(WooCommerceProductFactoryTestMixin):
    def test_woocommerce_content_update(self):
        product = self.create_test_product(
            sku="test_content_update",
            name="Test Content Update Product",
            assign_to_sales_channel=True,
        )

        factory = WooCommerceProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product
        )
        factory.run()

        translation = product.translations.get(
            language=self.company.language
        )

        translation.name = "Test Content Update name update"
        translation.description = "Test Content Update description update"
        translation.save()

        factory = WoocommerceProductContentUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=translation,
            local_product=product,
            remote_product=factory.remote_instance
        )
        factory.run()

        resp_product = self.api.get_product(factory.remote_instance.remote_id)
        self.assertEqual(resp_product['name'], translation.name)
        self.assertEqual(resp_product['description'], translation.description)
