from .mixins import TestCaseWoocommerceMixin
from django.conf import settings

from properties.models import Property, PropertyTranslation
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel, WoocommerceGlobalAttribute
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.factories.properties import WooCommerceGlobalAttributeCreateFactory


class WooCommercePropertyCreateFactoryTest(TestCaseWoocommerceMixin):
    def setUp(self):
        super().setUp()

        # Create a property for testing
        self.property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="test_property",
            type="select",
            is_public_information=True,
            add_to_filters=True
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.property,
            language=self.multi_tenant_company.language,
            name="Test Property"
        )

    def tearDown(self):
        # Clean up created attributes in WooCommerce
        try:
            # Get remote property instances
            remote_properties = WoocommerceGlobalAttribute.objects.filter(
                sales_channel=self.sales_channel
            )

            # Get API through the mixin
            api = GetWoocommerceAPIMixin()
            api.sales_channel = self.sales_channel
            api = api.get_api_client()

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
        initial_remote_props_count = WoocommerceGlobalAttribute.objects.filter(
            sales_channel=self.sales_channel,
            local_instance=self.property
        ).count()
        self.assertEqual(initial_remote_props_count, 0)

        # Create factory instance and run it
        factory = WooCommerceGlobalAttributeCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.property
        )
        factory.run()

        # Verify the remote property was created in database
        final_remote_props_count = WoocommerceGlobalAttribute.objects.filter(
            sales_channel=self.sales_channel,
            local_instance=self.property
        ).count()
        self.assertEqual(final_remote_props_count, 1)

        # Verify remote property details
        remote_property = WoocommerceGlobalAttribute.objects.get(
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
        factory = WooCommerceGlobalAttributeCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.property
        )
        factory.run()

        # Get the remote property data
        remote_property = WoocommerceGlobalAttribute.objects.get(
            sales_channel=self.sales_channel,
            local_instance=self.property
        )
        initial_remote_id = remote_property.remote_id

        # Now try to create it again - should reuse the existing one
        factory = WooCommerceGlobalAttributeCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.property
        )
        factory.run()

        # Verify we still have only one remote property
        count = WoocommerceGlobalAttribute.objects.filter(
            sales_channel=self.sales_channel,
            local_instance=self.property
        ).count()
        self.assertEqual(count, 1)

        # Verify the ID didn't change - we're reusing the same remote property
        remote_property.refresh_from_db()
        self.assertEqual(remote_property.remote_id, initial_remote_id)
