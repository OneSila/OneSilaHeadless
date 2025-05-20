

from .mixins import TestCaseWoocommerceMixin
from django.conf import settings
from django.db import transaction

from sales_channels.integrations.woocommerce.tests.helpers import CreateTestProductMixin
from media.tests.helpers import CreateImageMixin
from properties.models import Property, ProductPropertiesRule, ProductProperty, \
    ProductPropertiesRuleItem
from products.models import ConfigurableVariation
from sales_channels.integrations.woocommerce.models import WoocommerceProduct
from sales_channels.integrations.woocommerce.factories.products import (
    WooCommerceProductCreateFactory,
    WooCommerceProductUpdateFactory,
    WooCommerceProductDeleteFactory,
)
from sales_channels.integrations.woocommerce.factories.properties import WooCommerceGlobalAttributeCreateFactory

import logging
logger = logging.getLogger(__name__)


class WooCommerceProductFactoryTest(CreateTestProductMixin, CreateImageMixin, TestCaseWoocommerceMixin):
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

    def test_attribute_create(self):
        factory = WooCommerceGlobalAttributeCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.brand_property
        )
        factory.run()

    def test_woocom_simple_product(self):
        # Prepere a simple product that we will assign directly to the
        # sales channel
        product = self.create_test_product(
            sku="tshirt-simple-product",
            name="Test Product",
            assign_to_sales_channel=True,
            rule=self.product_rule
        )

        image = self.create_and_attach_image(product, fname='yellow.png')

        ProductProperty.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=self.brand_property,
            value_select=self.brand_property_value
        )

        ProductProperty.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=self.size_property,
            value_select=self.size_property_value_small
        )

        ProductProperty.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=self.type_property,
            value_select=self.tshirt_type
        )

        # Push the product remotely.
        factory = WooCommerceProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product
        )
        factory.run()

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
        resp_product = self.api.get_product(remote_product.remote_id)

        self.assertEqual(float(resp_product['price']), 812.00)
        self.assertEqual(resp_product['catalog_visibility'], 'hidden')
        self.assertEqual(resp_product['status'], 'draft')

    def test_woocom_configurable_product(self):
        # Prepare a config product that we will assign directly to the
        # sales channel
        parent = self.create_test_product(
            sku="tshirt-configurable-product",
            name="Test Product",
            assign_to_sales_channel=True,
            rule=self.product_rule,
            is_configurable=True
        )
        self.assertTrue(parent.is_configurable())

        image = self.create_and_attach_image(parent, fname='red.png')
        ProductProperty.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product=parent,
            property=self.type_property,
            value_select=self.tshirt_type
        )

        # Go and create the variations.
        small_product = self.create_test_product(
            sku="tshirt-config-small-product",
            name="Small Product",
            assign_to_sales_channel=True,
            rule=self.product_rule,
            is_configurable=False
        )
        self.assertTrue(small_product.is_simple())

        medium_product = self.create_test_product(
            sku="tshirt-config-medium-product",
            name="Medium Product",
            assign_to_sales_channel=True,
            rule=self.product_rule,
            is_configurable=False
        )
        self.assertTrue(medium_product.is_simple())

        large_product = self.create_test_product(
            sku="tshirt-config-large-product",
            name="Large Product",
            assign_to_sales_channel=True,
            rule=self.product_rule,
            is_configurable=False
        )
        self.assertTrue(large_product.is_simple())
        # Start assigngin the properties to the variations.
        variations = [small_product, medium_product, large_product]

        # Assign the properties to all variations.
        the_same_properties = [(self.brand_property, self.brand_property_value),
         (self.type_property, self.tshirt_type)]

        for product in variations:
            for t, v in the_same_properties:
                ProductProperty.objects.get_or_create(
                    multi_tenant_company=self.multi_tenant_company,
                    product=small_product,
                    property=t,
                    value_select=v
                )

        # Assing the sizes:
        ProductProperty.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product=small_product,
            property=self.size_property,
            value_select=self.size_property_value_small
        )

        ProductProperty.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product=medium_product,
            property=self.size_property,
            value_select=self.size_property_value_medium
        )

        ProductProperty.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product=large_product,
            property=self.size_property,
            value_select=self.size_property_value_large
        )

        # Assign the variations to the configurable product.
        for v in variations:
            ConfigurableVariation.objects.create(
                parent=parent,
                variation=v,
                multi_tenant_company=self.multi_tenant_company
            )

        # Push the product remotely.
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

        # Verify it exists in WooCommerce
        resp_product = self.api.get_product(remote_product.remote_id)
        self.assertIsNotNone(resp_product)
        self.assertEqual(resp_product['name'], parent.name)
        self.assertEqual(resp_product['sku'], parent.sku)

        # FIXME: This needs removing....
        input('pauze..........tick to continue....')

    def test_create_update_delete_product(self):
        """Test that WooCommerceProductCreateFactory properly creates a remote product"""
        product = self.create_test_product(
            sku="TEST-SKU-create-delete",
            name="Test Product",
            assign_to_sales_channel=True)

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
        resp_product = self.api.get_product(remote_product.remote_id)

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
            self.api.get_product(remote_product.remote_id)
