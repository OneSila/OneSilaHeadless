from .mixins import TestCaseWoocommerceMixin
from django.conf import settings
from django.db import transaction

from sales_channels.integrations.woocommerce.tests.helpers import CreateTestProductMixin
from media.tests.helpers import CreateImageMixin
from properties.models import Property, ProductPropertiesRule, ProductProperty, \
    ProductPropertiesRuleItem
from products.models import Product
from products.demo_data import (
    CONFIGURABLE_CHAIR_SKU,
    SIMPLE_TABLE_GLASS_SKU,
    SIMPLE_BED_QUEEN_SKU,
)
from sales_prices.models import SalesPrice
from core.tests import TestCaseDemoDataMixin
from sales_channels.integrations.woocommerce.models import WoocommerceProduct
from sales_channels.integrations.woocommerce.factories.products import (
    WooCommerceProductCreateFactory,
    WooCommerceProductUpdateFactory,
    WooCommerceProductDeleteFactory,
)
from sales_channels.integrations.woocommerce.exceptions import FailedToGetProductBySkuError
from sales_channels.integrations.woocommerce.factories.properties import WooCommerceGlobalAttributeCreateFactory

import logging
logger = logging.getLogger(__name__)


class WooCommerceProductFactoryTestMixin(CreateTestProductMixin, CreateImageMixin, TestCaseWoocommerceMixin):
    def setUp(self):
        super().setUp()
        # Setup a bunch of properties to create
        # the test products with.
        self.type_property = Property.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True,
        )

        self.size_property = self.create_property("Size", is_product_type=False)
        self.brand_property = self.create_property("Brand", is_product_type=False)

        self.tshirt_type = self.create_property_value("T-Shirt", prop=self.type_property)
        self.brand_property_value = self.create_property_value(name="OneSilaBrand", prop=self.brand_property)
        self.size_property_value_small = self.create_property_value(name="Small", prop=self.size_property)
        self.size_property_value_medium = self.create_property_value(name="Medium", prop=self.size_property)
        self.size_property_value_large = self.create_property_value(name="Large", prop=self.size_property)

        # Construct your rule to apply the product data to.
        self.product_rule, _ = ProductPropertiesRule.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.tshirt_type,
        )

        self.assertTrue(self.brand_property.id != self.size_property.id)
        self.assertTrue(self.type_property.id != self.size_property.id)

        # Verify that all property values have different IDs
        self.assertTrue(self.tshirt_type.id != self.brand_property_value.id)
        self.assertTrue(self.tshirt_type.id != self.size_property_value_small.id)
        self.assertTrue(self.tshirt_type.id != self.size_property_value_medium.id)
        self.assertTrue(self.tshirt_type.id != self.size_property_value_large.id)

        self.assertTrue(self.brand_property_value.id != self.size_property_value_small.id)
        self.assertTrue(self.brand_property_value.id != self.size_property_value_medium.id)
        self.assertTrue(self.brand_property_value.id != self.size_property_value_large.id)

        self.assertTrue(self.size_property_value_small.id != self.size_property_value_medium.id)
        self.assertTrue(self.size_property_value_small.id != self.size_property_value_large.id)
        self.assertTrue(self.size_property_value_medium.id != self.size_property_value_large.id)

        ProductPropertiesRuleItem.objects.create(
            rule=self.product_rule,
            property=self.brand_property,
            type=ProductPropertiesRuleItem.REQUIRED,
            sort_order=1,
            multi_tenant_company=self.multi_tenant_company,
        )

        ProductPropertiesRuleItem.objects.create(
            rule=self.product_rule,
            property=self.size_property,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
            sort_order=0,
            multi_tenant_company=self.multi_tenant_company,
        )


class WooCommerceProductFactoryTest(TestCaseDemoDataMixin, WooCommerceProductFactoryTestMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hard_remove_all_woocommerce_products_on_teardown = True

    def test_attribute_create(self):
        factory = WooCommerceGlobalAttributeCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.brand_property
        )
        factory.run()

    def test_woocom_simple_product(self):
        # Prepere a simple product that we will assign directly to the
        # sales channel
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
            sku=sku,
        )
        self.assign_product_to_sales_channel(product)

        # # Push the product remotely.
        # factory = WooCommerceProductCreateFactory(
        #     sales_channel=self.sales_channel,
        #     local_instance=product
        # )
        # factory.run()

        # logger.debug(f"WooCommerceProductFactoryTest factory.payload: {factory.payload}")

        # self.assertEqual(factory.payload['sku'], product.sku)

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
        product.active = False
        product.save()

        price = SalesPrice.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            currency=self.currency,
        )

        price.rrp = 2912
        price.price = 812
        price.save()

        # Update remote product instance and run it
        factory = WooCommerceProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=product
        )
        factory.run()

        # Verify the remote property was updated in database
        resp_product = self.api.get_product(remote_product.remote_id)

        self.assertEqual(float(resp_product['price']), price.price)
        self.assertEqual(float(resp_product['regular_price']), price.rrp)
        self.assertEqual(resp_product['catalog_visibility'], 'hidden')
        self.assertEqual(resp_product['status'], 'draft')

    def test_woocom_configurable_product(self):
        # Prepare a config product that we will assign directly to the
        # sales channel
        sku = CONFIGURABLE_CHAIR_SKU
        # first verify if the product is already created in woocomemrce
        # remove if yes
        try:
            remote_product = self.api.get_product_by_sku(sku)
            self.api.delete_product(remote_product['id'])
        except FailedToGetProductBySkuError:
            pass

        parent = Product.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            sku=sku
        )
        self.assertTrue(parent.configurable_variations.exists())
        self.assign_product_to_sales_channel(parent)

        for variation in parent.configurable_variations.all():
            self.assertEqual(variation.type, Product.SIMPLE)

        factory = WooCommerceProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=parent
        )
        factory.run()

        remote_product = WoocommerceProduct.objects.get(
            sales_channel=self.sales_channel,
            local_instance=parent
        )
        self.assertIsNotNone(remote_product.remote_id)

        # cleanup or other tests will fail.
        resp = self.api.get_product_by_sku(sku)
        self.api.delete_product(resp['id'])

    def test_create_update_delete_product(self):
        """Test that WooCommerceProductCreateFactory properly creates a remote product"""
        sku = SIMPLE_BED_QUEEN_SKU

        # first verify if the product is already created in woocomemrce
        # remove if yes
        try:
            remote_product = self.api.get_product_by_sku(sku)
            self.api.delete_product(remote_product['id'])
        except FailedToGetProductBySkuError:
            pass

        product = Product.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            sku=sku,
        )
        self.assign_product_to_sales_channel(product)

        # Find product-type properties for this product
        product_type_properties = Property.objects.filter(
            is_product_type=True,
            productproperty__product=product
        ).distinct()

        # We must create the product-type remotely to ensure we can try full payload test.
        logger.debug(f"Found {product_type_properties.count()} product-type properties for {product}")
        for prop in product_type_properties:
            # Create and run the attribute factory for each product-type property
            attribute_factory = WooCommerceGlobalAttributeCreateFactory(
                sales_channel=self.sales_channel,
                local_instance=prop
            )
            attribute_factory.run()

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
        resp_product = self.api.get_product(remote_product.remote_id)
        self.assertIsNotNone(resp_product)
        self.assertEqual(resp_product['name'], product.name)
        self.assertEqual(resp_product['sku'], product.sku)

        product.active = False
        product.save()

        price = SalesPrice.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            currency=self.currency,
        )

        price.rrp = 1000
        price.price = 100
        price.save()

        # Update remote product instance and run it
        factory = WooCommerceProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=product
        )
        factory.run()

        # Verify the remote property was updated in database
        resp_product = self.api.get_product(remote_product.remote_id)

        self.assertEqual(float(resp_product['price']), price.price)
        self.assertEqual(float(resp_product['regular_price']), price.rrp)
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
            self.api.get_product(remote_product.remote_id)
