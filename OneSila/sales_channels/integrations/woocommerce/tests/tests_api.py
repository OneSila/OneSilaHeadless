from core.tests import TestCase
from django.conf import settings

from sales_channels.integrations.woocommerce.api import WoocommerceApiWrapper
from sales_channels.integrations.woocommerce.exceptions import (
    FailedToGetError,
    FailedToGetAttributeError,
    FailedToGetAttributeTermsError,
)
from sales_channels.integrations.woocommerce.exceptions import DuplicateError


class WoocommerceApiWrapperTestCase(TestCase):
    """
    Test case for the WoocommerceApiWrapper class.
    """

    def setUp(self):
        """
        Set up the test case with a WoocommerceApiWrapper instance.
        """
        self.test_store_settings = settings.SALES_CHANNELS_INTEGRATIONS_TEST_STORES['WOOCOMMERCE']
        self.api_wrapper = WoocommerceApiWrapper(
            api_key=self.test_store_settings['api_key'],
            api_secret=self.test_store_settings['api_secret'],
            hostname=self.test_store_settings['hostname'],
            api_version=self.test_store_settings['api_version'],
            verify_ssl=self.test_store_settings.get('verify_ssl', False),
            timeout=self.test_store_settings.get('timeout', 10)
        )

    def test_get_attributes(self):
        """
        Test that get_attributes returns attributes data.
        """
        result = self.api_wrapper.get_attributes()

        self.assertIsInstance(result, list)
        if result:
            self.assertIn('id', result[0])
            self.assertIn('name', result[0])

    def test_get_attribute(self):
        """
        Test that get_attribute returns data for a specific attribute.
        """
        # First get all attributes to find a valid ID
        attributes = self.api_wrapper.get_attributes()
        if not attributes:
            self.skipTest("No attributes available to test get_attribute")

        attribute_id = attributes[0]['id']
        result = self.api_wrapper.get_attribute(attribute_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['id'], attribute_id)
        self.assertIn('name', result)

    def test_get_attribute_terms(self):
        """
        Test that get_attribute_terms returns terms for a specific attribute.
        """
        # First get all attributes to find a valid ID
        attributes = self.api_wrapper.get_attributes()
        if not attributes:
            self.skipTest("No attributes available to test get_attribute_terms")

        attribute_id = attributes[0]['id']
        result = self.api_wrapper.get_attribute_terms(attribute_id)

        self.assertIsInstance(result, list)
        # Terms might be empty, so only check structure if there are terms
        if result:
            self.assertIn('id', result[0])
            self.assertIn('name', result[0])

    def test_get_products(self):
        """
        Test that get_products returns products data.
        """
        result = self.api_wrapper.get_products()

        self.assertIsInstance(result, list)
        if result:
            self.assertIn('id', result[0])
            self.assertIn('name', result[0])

    def test_get_with_invalid_endpoint(self):
        """
        Test that get raises the correct exception when the API call fails.
        """
        with self.assertRaises(FailedToGetError):
            self.api_wrapper.get('invalid/endpoint')

    def test_get_attribute_error(self):
        """
        Test that get_attribute raises the correct exception when get fails.
        """
        with self.assertRaises(FailedToGetAttributeError):
            # Use an ID that's unlikely to exist
            self.api_wrapper.get_attribute(999999)

    def test_get_attribute_terms_error(self):
        """
        Test that get_attribute_terms raises the correct exception when get fails.
        """
        with self.assertRaises(FailedToGetAttributeTermsError):
            # Use an ID that's unlikely to exist
            self.api_wrapper.get_attribute_terms(999999)

    def test_get_attribute_by_code(self):
        """
        Test that get_attribute_by_code returns the correct attribute.
        """
        try:
            self.api_wrapper.create_attribute('colour', 'Colour')
        except DuplicateError:
            pass
        result = self.api_wrapper.get_attribute_by_code('colour')
        self.assertIsInstance(result, dict)
        self.assertEqual(result['slug'], 'colour')

    def test_get_attribute_by_code_not_found(self):
        """
        Test that get_attribute_by_code raises the correct exception when the attribute is not found.
        """
        with self.assertRaises(FailedToGetAttributeError):
            self.api_wrapper.get_attribute_by_code('non-existent-attribute')

    def test_create_and_delete_attribute(self):
        """
        Test that create_attribute creates an delete an attribute successfully.
        """
        result = self.api_wrapper.create_attribute('test-attribute', 'Test Attribute')
        self.assertIsInstance(result, dict)
        self.assertEqual(result['slug'], 'test-attribute')
        self.assertEqual(result['name'], 'Test Attribute')
        self.assertEqual(result['type'], 'select')

        result = self.api_wrapper.delete_attribute(result['id'])
        self.assertTrue(result)

    def test_create_and_delete_attribute_term(self):
        """
        Test that create_attribute_term creates an delete an attribute term successfully.
        """
        # Create an attribute
        attribute_result = self.api_wrapper.create_attribute('test-attribute-term-test', 'Test Attribute')
        # Create an attribute value
        result = self.api_wrapper.create_attribute_term(attribute_result['id'], 'Test Attribute Term')
        self.assertIsInstance(result, dict)
        self.api_wrapper.delete_attribute_term(attribute_result['id'], result['id'])
        self.api_wrapper.delete_attribute(attribute_result['id'])

    def test_create_and_delete_product_woocommerce(self):
        """
        Test that create_product creates an delete a product successfully.
        """
        kwargs = {
            'name': 'Test Product',
            'type': 'simple',
            'sku': 'TEST-PRODUCT-001',
            'status': 'publish',
            'catalog_visibility': 'visible',
            'regular_price': '0.9',
            'sale_price': '0.8',
        }
        result = self.api_wrapper.create_product(**kwargs)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['name'], 'Test Product')

        result = self.api_wrapper.delete_product(result['id'])
        self.assertTrue(result)

    def test_create_duplicate_product_woocommerce(self):
        """
        Test that create_product raises a DuplicateError when the product already exists.
        """
        kwargs = {
            'name': 'Test Product',
            'type': 'simple',
            'sku': 'TEST-PRODUCT-DUPLICATE',
            'status': 'publish',
            'catalog_visibility': 'visible',
            'regular_price': 0.9,
            'sale_price': 0.8,
        }
        result = self.api_wrapper.create_product(**kwargs)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['name'], 'Test Product')

        self.assertTrue(result)
        with self.assertRaises(DuplicateError):
            self.api_wrapper.create_product(**kwargs)

        result = self.api_wrapper.delete_product(result['id'])

    def test_create_product_and_add_img(self):
        kwargs = {
            'name': 'Test test_create_product_and_add_img',
            'type': 'simple',
            'sku': 'TEST-PRODUCT-IMG-ADD',
            'status': 'publish',
            'catalog_visibility': 'visible',
            'regular_price': '0.9',
            'sale_price': '0.8',
            'images': [{"src": 'https://www.onesila.com/media/images/Frame_666_JLKFadU.2e16d0ba.fill-1200x1200.png'}]
        }
        result = self.api_wrapper.create_product(**kwargs)

        extra_img = [{"src": 'https://www.onesila.com/media/images/Frame_666_JLKFadU.2e16d0ba.fill-1200x1200.png'},
            {"src": 'https://www.onesila.com/static/images/logo.png'}]
        result = self.api_wrapper.update_product(result['id'], images=extra_img)
        result = self.api_wrapper.delete_product(result['id'])

    def test_create_full_configurable_product_woocommerce(self):
        """
        Test that create_product creates a full configurable product successfully.

        Use this as an example to populate the factories.

        It's important to understand that in woocommerce the shared attributes are populated on the
        configurable product.  And the variation "configurator" attributes are populated on the
        variation products only.

        Also you must understand that filterable attributes go on the configurable product as a "global attribute"
        The non filterable attributes go on the viations directly and are untracked.

        On the variations you will find that a direct attribute was added.
        You will find that the call doesnt fail. But neither are they added.
        """
        size_attribute = {
            "name": "Size",
            "slug": "size_tshirt_test",
            "type": "select",
            "has_archives": False
        }
        product_type_attribute = {
            "name": "Product Type",
            "slug": "product_type_tshirt_test",
            "type": "select",
            "has_archives": False
        }
        try:
            size_attribute_response = self.api_wrapper.create_attribute(**size_attribute)
            size_attribute_id = size_attribute_response['id']
        except DuplicateError:
            size_attribute_id = self.api_wrapper.get_attribute_by_code('size_tshirt_test')['id']

        try:
            product_type_attribute_response = self.api_wrapper.create_attribute(**product_type_attribute)
            product_type_attribute_id = product_type_attribute_response['id']
        except DuplicateError:
            product_type_attribute_id = self.api_wrapper.get_attribute_by_code('product_type_tshirt_test')['id']

        config_product = {
            "name": "API Test TShirt",
            "type": "variable",
            "sku": "tshirt-configurable-product",
            "regular_price": "1.0",
            # "sale_price": "0.9",
            "status": "publish",
            "catalog_visibility": "visible",
            "description": "<b>Description</b>",
            "short_description": "<b>Short Description</b>",
            "images": [
                {
                    # This url is always an image.
                    "src": "https://www.onesila.com/testing/664551190f3efefd0d6a52607fa39059.jpg"
                }
            ],
            "attributes": [
                {
                    'id': product_type_attribute_id,
                    "options": ["T-Shirt"],
                    "visible": True,
                    "variation": False
                },
                {
                    "id": size_attribute_id,
                    "options": ["Small", "Medium", "Large"],
                    "visible": True,
                    "variation": True
                },
                {
                    # This attribute will only show on the configurable
                    # product and is not able to have filters due to it's local
                    # nature.
                    'name': 'Material',
                    'options': ['100% Cotton'],
                    'visible': True,
                    'variation': False
                }

            ]
        }

        config_product_result = self.api_wrapper.create_product(**config_product)
        config_product_result_id = config_product_result['id']
        self.assertIsInstance(config_product_result, dict)
        self.assertEqual(config_product_result['name'], config_product['name'])

        variations_small = {
            'name': 'Small',
            'sku': 'TEST-VARIATION-SMALL',
            'regular_price': '1.0',
            'sale_price': '0.9',
            'attributes': [
                {
                    'id': size_attribute_id,
                    'option': 'Small'
                },
                {
                    'id': product_type_attribute_id,
                    'option': 'T-Shirt'
                },
                {
                    'name': 'Material',
                    'option': 'Cotton'
                }
            ]
        }
        variations_medium = {
            'name': 'Medium',
            'sku': 'TEST-VARIATION-MEDIUM',
            'regular_price': '1.1',
            'sale_price': '1.0',
            'attributes': [
                {
                    'id': size_attribute_id,
                    'option': 'Medium'
                },
                {
                    'id': product_type_attribute_id,
                    'option': 'T-Shirt'
                },
                {
                    'name': 'Material',
                    'option': 'Cotton'
                }
            ]
        }
        variations_large = {
            'name': 'Large',
            'sku': 'TEST-VARIATION-LARGE',
            'regular_price': '1.2',
            'sale_price': '1.1',
            'attributes': [
                {
                    'id': size_attribute_id,
                    'option': 'Large'
                },
                {
                    'id': product_type_attribute_id,
                    'option': 'T-Shirt'
                },
                {
                    'name': 'Material',
                    'option': 'Cotton'
                }
            ]
        }

        variations_small_result = self.api_wrapper.create_product_variation(config_product_result_id, **variations_small)
        self.assertIsInstance(variations_small_result, dict)
        self.assertEqual(variations_small_result['name'], variations_small['name'])

        variations_medium_result = self.api_wrapper.create_product_variation(config_product_result_id, **variations_medium)
        self.assertIsInstance(variations_medium_result, dict)
        self.assertEqual(variations_medium_result['name'], variations_medium['name'])

        variations_large_result = self.api_wrapper.create_product_variation(config_product_result_id, **variations_large)
        self.assertIsInstance(variations_large_result, dict)
        self.assertEqual(variations_large_result['name'], variations_large['name'])

        # Delete the attribute and products.
        result = self.api_wrapper.delete_attribute(size_attribute_id)
        self.assertTrue(result)
        result = self.api_wrapper.delete_product(config_product_result['id'])
        self.assertTrue(result)
