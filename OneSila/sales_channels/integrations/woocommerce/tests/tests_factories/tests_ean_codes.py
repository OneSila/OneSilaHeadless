from .tests_products import WooCommerceProductFactoryTestMixin
from sales_channels.integrations.woocommerce.factories.products import (
    WooCommerceProductCreateFactory,
)
from sales_channels.integrations.woocommerce.factories.content import WoocommerceProductContentUpdateFactory
from sales_channels.integrations.woocommerce.factories.ean import WooCommerceEanCodeUpdateFactory

from core.tests import TestCaseDemoDataMixin

from products.demo_data import SIMPLE_TABLE_GLASS_SKU, CONFIGURABLE_CHAIR_SKU
from products.models import Product

import logging
logger = logging.getLogger(__name__)


class WooCommerceEanCodeFactoryTestCase(TestCaseDemoDataMixin, WooCommerceProductFactoryTestMixin):
    def __init__(self, *args, **kwargs):
        self.remove_woocommerce_mirror_and_remote_on_teardown = True
        super().__init__(*args, **kwargs)

    def test_woocommerce_ean_code_factory(self):
        product = Product.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            sku=SIMPLE_TABLE_GLASS_SKU
        )

        self.assign_product_to_sales_channel(product)
        self.assertEqual(product.eancode_set.exists(), True)
        ean_code = product.eancode_set.first()

        factory = WooCommerceProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product
        )
        factory.run()
        remote_instance = factory.remote_instance
        self.assertTrue(remote_instance.remote_id is not None)

        factory = WooCommerceEanCodeUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_product=factory.remote_instance
        )
        factory.run()

        resp = self.api.get_product(remote_instance.remote_id)
        self.assertEqual(resp['global_unique_id'], ean_code.ean_code)

    def test_woocommerce_ean_code_factory_config_variation(self):
        product = Product.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            sku=CONFIGURABLE_CHAIR_SKU
        )
        child = product.configurable_variations.first()

        ean_code = child.eancode_set.first()
        if not ean_code:
            ean_code = child.eancode_set.create(
                multi_tenant_company=self.multi_tenant_company,
                ean_code='1234567890124'
            )

        # Assign the product to the sales channel
        self.assign_product_to_sales_channel(child)

        factory = WooCommerceProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=child
        )
        factory.run()
        remote_instance = factory.remote_instance

        factory = WooCommerceEanCodeUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=child,
            remote_product=factory.remote_instance
        )
        factory.run()

        resp = self.api.get_product(remote_instance.remote_id)
        self.assertEqual(resp['global_unique_id'], ean_code.ean_code)
