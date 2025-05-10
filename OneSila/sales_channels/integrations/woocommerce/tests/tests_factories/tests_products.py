

from .mixins import TestCaseWoocommerceMixin
from django.conf import settings
from django.db import transaction

from sales_channels.integrations.woocommerce.tests.helpers import CreateTestProductMixin
from properties.models import Property, PropertyTranslation, PropertySelectValue, PropertySelectValueTranslation
from products.models import Product, ProductTranslation
from sales_channels.integrations.woocommerce.models import WoocommerceProduct, WoocommerceCurrency
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
        product = self.create_test_product(sku="TEST-SKU-001-create-delete", name="Test Product")

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
        resp_product = api.get_product(remote_product.remote_id)
        self.assertIsNotNone(resp_product)
        self.assertEqual(resp_product['name'], product.name)
        self.assertEqual(resp_product['sku'], product.sku)

        product.active = False
        product.save()

        with transaction.atomic():
            self.price.rrp = 2912
            self.price.price = 812
            self.price.save()

        # Update remote product instance and run it
        factory = WooCommerceProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=product
        )
        factory.run()

        # Verify the remote property was updated in database
        resp_product = api.get_product(remote_product.remote_id)

        self.assertEqual(float(resp_product['price']), 812.00)
        self.assertEqual(resp_product['catalog_visibility'], 'hidden')
        self.assertEqual(resp_product['status'], 'draft')

        # cleanup
        factory = WooCommerceProductDeleteFactory(
            sales_channel=self.sales_channel,
            local_instance=product
        )
        factory.run()

        # ensure it's deleted
        with self.assertRaises(Exception):
            api.get_product(remote_product.remote_id)
