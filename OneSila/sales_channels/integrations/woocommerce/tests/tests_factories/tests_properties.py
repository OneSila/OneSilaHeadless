from .mixins import TestCaseWoocommerceMixin
from django.conf import settings

from properties.models import Property, PropertyTranslation, PropertySelectValue, PropertySelectValueTranslation
from sales_channels.integrations.woocommerce.models import WoocommerceGlobalAttribute, WoocommerceGlobalAttributeValue
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.factories.properties import (
    WooCommerceGlobalAttributeCreateFactory,
    WooCommerceGlobalAttributeUpdateFactory,
    WooCommerceGlobalAttributeDeleteFactory,
    WoocommerceGlobalAttributeValueCreateFactory,
    WoocommerceGlobalAttributeValueUpdateFactory,
    WoocommerceGlobalAttributeValueDeleteFactory,
)

import logging
logger = logging.getLogger(__name__)


class WooCommercePropertyFactoryTest(TestCaseWoocommerceMixin):
    def setUp(self):
        super().setUp()

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
        prop = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="test_property",
            type="select",
            is_public_information=True,
            add_to_filters=True
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=prop,
            language=self.multi_tenant_company.language,
            name="Test Property"
        )

        # Create factory instance and run it
        factory = WooCommerceGlobalAttributeCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=prop
        )
        factory.run()

        # Verify the remote property was created in database
        remote_prop = WoocommerceGlobalAttribute.objects.get(
            sales_channel=self.sales_channel,
            local_instance=prop
        )
        self.assertIsNotNone(remote_prop.remote_id)

        # Verify it exists in WooCommerce
        api = factory.get_api()
        attribute = api.get_attribute(remote_prop.remote_id)
        self.assertIsNotNone(attribute)
        self.assertEqual(attribute['name'], prop.name)
        self.assertEqual(attribute['slug'], prop.internal_name)

        # cleanup
        api.delete_attribute(remote_prop.remote_id)

        # ensure it's deleted
        with self.assertRaises(Exception):
            api.get_attribute(remote_prop.remote_id)

    def test_update_attribute_property(self):
        """Test that WooCommercePropertyUpdateFactory properly updates a remote property"""
        # Create a property
        prop = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="update_test_property",
            type="select",
            is_public_information=True,
            add_to_filters=True
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=prop,
            language=self.multi_tenant_company.language,
            name="Update Test Property"
        )

        # Create the remote property first
        create_factory = WooCommerceGlobalAttributeCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=prop
        )
        create_factory.run()
        remote_prop = WoocommerceGlobalAttribute.objects.get(
            sales_channel=self.sales_channel,
            local_instance=prop
        )
        # Update the property name
        PropertyTranslation.objects.filter(
            property=prop,
            language=self.multi_tenant_company.language
        ).update(name="Updated Property Name")

        # Create update factory instance and run it
        update_factory = WooCommerceGlobalAttributeUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=prop,
            remote_instance=remote_prop
        )
        update_factory.run()

        # Verify it was updated in WooCommerce
        api = update_factory.get_api()
        updated_attribute = api.get_attribute(remote_prop.remote_id)
        self.assertIsNotNone(updated_attribute)
        self.assertEqual(updated_attribute['name'], "Updated Property Name")
        self.assertEqual(updated_attribute['slug'], prop.internal_name)

        # cleanup
        api.delete_attribute(remote_prop.remote_id)

        # ensure it's deleted
        with self.assertRaises(Exception):
            api.get_attribute(remote_prop.remote_id)

    def test_delete_attribute(self):
        """Test deleting a WooCommerce global attribute"""
        # Create a property to delete
        prop = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="delete_test_property",
            type="select",
            is_public_information=True,
            add_to_filters=True
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=prop,
            language=self.multi_tenant_company.language,
            name="Delete Test Property"
        )

        # Create the remote property first
        create_factory = WooCommerceGlobalAttributeCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=prop
        )
        create_factory.run()
        remote_prop = WoocommerceGlobalAttribute.objects.get(
            sales_channel=self.sales_channel,
            local_instance=prop
        )

        # Verify it exists in WooCommerce
        api = create_factory.get_api()
        attribute = api.get_attribute(remote_prop.remote_id)
        self.assertIsNotNone(attribute)

        # Create delete factory instance and run it
        delete_factory = WooCommerceGlobalAttributeDeleteFactory(
            sales_channel=self.sales_channel,
            remote_instance=remote_prop
        )
        delete_factory.run()

        # Verify it was deleted from WooCommerce
        with self.assertRaises(Exception):
            api.get_attribute(remote_prop.remote_id)


class WooCommercePropertyValueFactoryTest(TestCaseWoocommerceMixin):
    def test_create_property_value(self):
        """Test that WooCommercePropertyValueCreateFactory properly creates a remote property value"""
        prop = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="test_create_property_value",
            type="select",
            is_public_information=True,
            add_to_filters=True
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=prop,
            language=self.multi_tenant_company.language,
            name="Test Property for Values"
        )

        # Create the remote property
        create_factory = WooCommerceGlobalAttributeCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=prop
        )
        create_factory.run()
        remote_property = WoocommerceGlobalAttribute.objects.get(
            sales_channel=self.sales_channel,
            local_instance=prop
        )
        api = create_factory.get_api()

        # Create a property value
        property_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=prop,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=property_value,
            language=self.multi_tenant_company.language,
            value="Test Value"
        )

        # Create factory instance and run it
        factory = WoocommerceGlobalAttributeValueCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=property_value,
        )
        factory.run()

        # Verify the property value was created in WooCommerce
        remote_value = WoocommerceGlobalAttributeValue.objects.get(
            sales_channel=self.sales_channel,
            local_instance=property_value
        )
        self.assertIsNotNone(remote_value)
        self.assertIsNotNone(remote_value.remote_id)

        # Verify it exists in WooCommerce API
        remote_attribute_value = api.get_attribute_term(remote_property.remote_id, remote_value.remote_id)
        self.assertTrue(int(remote_attribute_value['id']) == int(remote_value.remote_id))

        # cleanup
        api.delete_attribute_term(remote_property.remote_id, remote_value.remote_id)
        api.delete_attribute(remote_property.remote_id)

        # ensure it's deleted
        with self.assertRaises(Exception):
            api.get_attribute_term(remote_property.remote_id, remote_value.remote_id)

    def test_update_property_value(self):
        """Test that WooCommercePropertyValueCreateFactory properly creates a remote property value"""
        prop = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="test_create_property_value",
            type="select",
            is_public_information=True,
            add_to_filters=True
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=prop,
            language=self.multi_tenant_company.language,
            name="Test Property for Values"
        )

        # Create the remote property
        create_factory = WooCommerceGlobalAttributeCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=prop
        )
        create_factory.run()
        remote_property = WoocommerceGlobalAttribute.objects.get(
            sales_channel=self.sales_channel,
            local_instance=prop
        )
        api = create_factory.get_api()

        # Create a property value
        property_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=prop,
        )
        translation = PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=property_value,
            language=self.multi_tenant_company.language,
            value="Test Value"
        )

        # Create factory instance and run it
        factory = WoocommerceGlobalAttributeValueCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=property_value,
        )
        factory.run()
        remote_property_value = WoocommerceGlobalAttributeValue.objects.get(
            sales_channel=self.sales_channel,
            local_instance=property_value
        )

        # Update the property value
        translation.value = "Updated Value"
        translation.save()

        # Create update factory instance and run it
        update_factory = WoocommerceGlobalAttributeValueUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=property_value,
            remote_instance=remote_property_value
        )
        update_factory.run()

        # Verify it was updated in WooCommerce
        updated_value = api.get_attribute_term(remote_property.remote_id, remote_property_value.remote_id)
        self.assertEqual(updated_value['name'], "Updated Value")

        # cleanup
        factory = WoocommerceGlobalAttributeValueDeleteFactory(
            sales_channel=self.sales_channel,
            remote_instance=remote_property_value
        )
        factory.run()

        # ensure it's deleted
        with self.assertRaises(Exception):
            api.get_attribute_term(remote_property.remote_id, remote_property_value.remote_id)

        api.delete_attribute(remote_property.remote_id)
