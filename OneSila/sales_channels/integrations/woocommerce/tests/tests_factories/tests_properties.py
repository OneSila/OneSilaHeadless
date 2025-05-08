from core.tests import TestCase
from django.conf import settings

from properties.models import Property
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel, WoocommerceAttribute
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.factories.properties import WooCommercePropertyCreateFactory


class WooCommercePropertyCreateFactoryTest(TestCase):
    def setUp(self):
        super().setUp()

        # Get test store settings from settings.py
        self.test_store_settings = settings.SALES_CHANNELS_INTEGRATIONS_TEST_STORES['WOOCOMMERCE']

        # Create a sales channel for testing with test store credentials
        self.sales_channel = WoocommerceSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="Test WooCommerce Store",
            hostname=self.test_store_settings['hostname'],
            consumer_key=self.test_store_settings['api_key'],
            consumer_secret=self.test_store_settings['api_secret']
        )

        # Create a property for testing
        self.property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="test_property",
            code="test_property_code",
            type="select",
            is_public_information=True,
            add_to_filters=True
        )

    def tearDown(self):
        # Clean up created attributes in WooCommerce
        try:
            # Get remote property instances
            remote_properties = WoocommerceAttribute.objects.filter(
                sales_channel=self.sales_channel
            )

            # Get API through the mixin
            api = GetWoocommerceAPIMixin(sales_channel=self.sales_channel).get_api_client()

            # Delete each property
            for remote_property in remote_properties:
                try:
                    api.delete_attribute(remote_property.remote_id)
                except Exception:
                    pass

        except Exception:
            pass

        super().tearDown()

    def test_create_property(self):
        """Test that WooCommercePropertyCreateFactory properly creates a remote property"""
        # Initial state check
        initial_remote_props_count = WoocommerceAttribute.objects.filter(
            sales_channel=self.sales_channel,
            local_instance=self.property
        ).count()
        self.assertEqual(initial_remote_props_count, 0)

        # Create factory instance and run it
        factory = WooCommercePropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.property
        )
        factory.run()

        # Verify the remote property was created in database
        final_remote_props_count = WoocommerceAttribute.objects.filter(
            sales_channel=self.sales_channel,
            local_instance=self.property
        ).count()
        self.assertEqual(final_remote_props_count, 1)

        # Verify remote property details
        remote_property = WoocommerceAttribute.objects.get(
            sales_channel=self.sales_channel,
            local_instance=self.property
        )
        self.assertIsNotNone(remote_property.remote_id)

        # Verify it exists in WooCommerce
        api = factory.get_api()
        attribute = api.get_attribute(remote_property.remote_id)
        self.assertIsNotNone(attribute)
        self.assertEqual(attribute['name'], self.property.name)
        self.assertEqual(attribute['slug'], self.property.code)

    def test_fetch_existing_property(self):
        """Test that factory updates existing property rather than creating a new one"""
        # First create the property
        factory = WooCommercePropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.property
        )
        factory.run()

        # Get the remote property data
        remote_property = WoocommerceAttribute.objects.get(
            sales_channel=self.sales_channel,
            local_instance=self.property
        )
        initial_remote_id = remote_property.remote_id

        # Now try to create it again - should reuse the existing one
        factory = WooCommercePropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.property
        )
        factory.run()

        # Verify we still have only one remote property
        count = WoocommerceAttribute.objects.filter(
            sales_channel=self.sales_channel,
            local_instance=self.property
        ).count()
        self.assertEqual(count, 1)

        # Verify the ID didn't change - we're reusing the same remote property
        remote_property.refresh_from_db()
        self.assertEqual(remote_property.remote_id, initial_remote_id)

    def test_property_type_mapping(self):
        """Test that property types are correctly mapped"""
        # Create a text property
        text_property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="text_property",
            code="text_property_code",
            type="text"
        )

        # Create factory instance and run it
        factory = WooCommercePropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=text_property
        )
        factory.run()

        # Get the created remote property
        remote_property = WoocommerceAttribute.objects.get(
            sales_channel=self.sales_channel,
            local_instance=text_property
        )

        # Verify the type in WooCommerce
        api = factory.get_api()
        attribute = api.get_attribute(remote_property.remote_id)
        self.assertEqual(attribute['type'], 'text')
