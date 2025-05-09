

from .mixins import TestCaseWoocommerceMixin
from django.conf import settings

from sales_channels.tests.helpers import CreateTestProductMixin
from properties.models import Property, PropertyTranslation, PropertySelectValue, PropertySelectValueTranslation
from products.models import Product, ProductTranslation
from sales_channels.integrations.woocommerce.models import WoocommerceProduct
from sales_channels.integrations.woocommerce.factories.products import (
    WooCommerceProductCreateFactory,
    WooCommerceProductUpdateFactory,
    WooCommerceProductDeleteFactory,
)

import logging
logger = logging.getLogger(__name__)


class WooCommerceProductFactoryTest(CreateTestProductMixin, TestCaseWoocommerceMixin):
    def test_create_update_delete_product(self):
        """Test that WooCommerceProductCreateFactory properly creates a remote product"""

        product = self.create_test_product(sku="TEST-SKU-001", name="Test Product")

        # Create factory instance and run it
        factory = WooCommerceProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product
        )
        factory.run()

        # Verify the remote property was created in database
        remote_product = WoocommerceProduct.objects.get(
            sales_channel=self.sales_channel,
            local_instance=product
        )
        self.assertIsNotNone(remote_product.remote_id)

        # Verify it exists in WooCommerce
        api = factory.get_api()
        product = api.get_product(remote_product.remote_id)
        self.assertIsNotNone(product)
        self.assertEqual(product['name'], product.name)
        self.assertEqual(product['sku'], product.sku)

        product.active = False
        product.save()

        # Update remote product instance and run it
        factory = WooCommerceProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=product
        )
        factory.run()

        # Verify the remote property was updated in database
        product = api.get_product(remote_product.remote_id)
        self.assertEqual(product['active'], False)

        # cleanup
        factory = WooCommerceProductDeleteFactory(
            sales_channel=self.sales_channel,
            local_instance=product
        )
        factory.run()

        # ensure it's deleted
        with self.assertRaises(Exception):
            api.get_product(remote_product.remote_id)
