from .tests_products import WooCommerceProductFactoryTestMixin
from sales_channels.integrations.woocommerce.factories.products import (
    WooCommerceProductCreateFactory,
)
from sales_channels.integrations.woocommerce.factories.content import WoocommerceProductContentUpdateFactory
from sales_channels.integrations.woocommerce.factories.ean import WooCommerceEanCodeUpdateFactory
from sales_channels.integrations.woocommerce.exceptions import FailedToGetProductBySkuError
from core.tests import TestCaseDemoDataMixin

from products.demo_data import SIMPLE_TABLE_GLASS_SKU, CONFIGURABLE_CHAIR_SKU
from products.models import Product

import logging

from ...models import WoocommerceProduct

logger = logging.getLogger(__name__)


class WooCommerceEanCodeFactoryTestCase(TestCaseDemoDataMixin, WooCommerceProductFactoryTestMixin):
    def __init__(self, *args, **kwargs):
        self.remove_woocommerce_mirror_and_remote_on_teardown = True
        super().__init__(*args, **kwargs)

    def test_woocommerce_ean_code_factory(self):
        sku = SIMPLE_TABLE_GLASS_SKU
        # first verify if the product is already created in woocomemrce
        # remove if yes
        try:
            remote_product = self.api.get_product_by_sku(sku)
            self.api.delete_product(remote_product['id'])
        except FailedToGetProductBySkuError:
            pass

        product = Product.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            sku=sku
        )

        self.assign_product_to_sales_channel(product)
        self.assertEqual(product.eancode_set.exists(), True)
        ean_code = product.eancode_set.first()

        remote_instance = WoocommerceProduct.objects.get(local_instance=product)
        self.assertTrue(remote_instance.remote_id is not None)

        factory = WooCommerceEanCodeUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_product=remote_instance
        )
        factory.run()

        resp = self.api.get_product(remote_instance.remote_id)
        self.assertEqual(resp['global_unique_id'], ean_code.ean_code)

    def test_woocommerce_ean_code_factory_config_variation(self):
        sku = CONFIGURABLE_CHAIR_SKU
        # first verify if the product is already created in woocomemrce
        # remove if yes
        try:
            self.api.delete_product_by_sku(sku)
        except FailedToGetProductBySkuError:
            pass

        product = Product.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            sku=sku
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

        remote_instance = WoocommerceProduct.objects.get(local_instance=child)
        factory = WooCommerceEanCodeUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=child,
            remote_product=remote_instance
        )
        factory.run()

        resp = self.api.get_product(remote_instance.remote_id)
        self.assertEqual(resp['global_unique_id'], ean_code.ean_code)

        # cleanup or other tests will fail.
        self.api.delete_product(resp['id'])
