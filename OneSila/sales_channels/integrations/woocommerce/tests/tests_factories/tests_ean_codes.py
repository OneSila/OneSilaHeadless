from .tests_products import WooCommerceProductFactoryTestMixin
from sales_channels.integrations.woocommerce.factories.products import (
    WooCommerceProductCreateFactory,
)
from sales_channels.integrations.woocommerce.factories.content import WoocommerceProductContentUpdateFactory
from sales_channels.integrations.woocommerce.factories.ean import WooCommerceEanCodeUpdateFactory

import logging
logger = logging.getLogger(__name__)


class WooCommerceEanCodeFactoryTest(WooCommerceProductFactoryTestMixin):
    def test_woocommerce_ean_code_factory(self):
        product = self.create_test_product(
            sku="test_ean_code",
            name="Test EAN Code Product",
            assign_to_sales_channel=True,
        )

        factory = WooCommerceProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product
        )
        factory.run()

        ean_code = product.eancode_set.create(
            ean_code='1234567890123',
            multi_tenant_company=self.multi_tenant_company
        )

        factory = WooCommerceEanCodeUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_product=factory.remote_instance
        )
        factory.run()

        resp = self.api.get_product(factory.remote_instance.remote_id)
        self.assertEqual(resp['global_unique_id'], '1234567890123')
