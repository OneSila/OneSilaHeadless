from core.tests import TestCase
from django.core.exceptions import ValidationError
from properties.models import (
    ProductProperty,
    Property,
    PropertySelectValue,
    PropertySelectValueTranslation,
)
from products.models import Product
from sales_channels.integrations.amazon.models.sales_channels import AmazonSalesChannel
from sales_channels.models.properties import RemoteProperty, RemotePropertySelectValue


class PropertyManagerGetOrCreateTestCase(TestCase):
    def test_get_or_create_auto_increment_internal_name(self):
        """Ensure a unique internal_name is generated for each call."""
        # Existing property with internal_name "color"
        Property.objects.create(
            internal_name="color",
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )

        prop1, created1 = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
            internal_name="color",
        )
        self.assertTrue(created1)
        self.assertEqual(prop1.internal_name, "color_1")

        prop2, created2 = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
            internal_name="color",
        )
        self.assertFalse(created2)
        self.assertEqual(prop2.internal_name, "color_1")


class PropertySelectValueMergeTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.prop = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        self.value1 = PropertySelectValue.objects.create(
            property=self.prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.value2 = PropertySelectValue.objects.create(
            property=self.prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.target = PropertySelectValue.objects.create(
            property=self.prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.value1,
            language=self.multi_tenant_company.language,
            value="Red",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.value2,
            language=self.multi_tenant_company.language,
            value="Blue",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.product_property = ProductProperty.objects.create(
            product=self.product,
            property=self.prop,
            multi_tenant_company=self.multi_tenant_company,
            value_select=self.value1,
        )

    def test_merge(self):
        PropertySelectValue.objects.filter(id__in=[self.value1.id, self.value2.id]).merge(self.target)

        self.assertFalse(
            PropertySelectValue.objects.filter(id__in=[self.value1.id, self.value2.id]).exists()
        )
        self.product_property.refresh_from_db()
        self.assertEqual(self.product_property.value_select_id, self.target.id)

    def test_merge_different_property(self):
        other_prop = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        other_value = PropertySelectValue.objects.create(
            property=other_prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        with self.assertRaises(ValidationError):
            PropertySelectValue.objects.filter(id=self.value1.id).merge(other_value)


class PropertySelectValueMergeRemoteTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.prop = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        self.value1 = PropertySelectValue.objects.create(
            property=self.prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.target = PropertySelectValue.objects.create(
            property=self.prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.sales_channel = AmazonSalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_property = RemoteProperty.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_value_source = RemotePropertySelectValue.objects.create(
            sales_channel=self.sales_channel,
            remote_property=self.remote_property,
            local_instance=self.value1,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_value_target = RemotePropertySelectValue.objects.create(
            sales_channel=self.sales_channel,
            remote_property=self.remote_property,
            local_instance=self.target,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_merge_when_remote_select_value_exists(self):
        PropertySelectValue.objects.filter(id=self.value1.id).merge(self.target)

        self.assertFalse(
            RemotePropertySelectValue.objects.filter(id=self.remote_value_source.id).exists()
        )
        self.assertEqual(
            RemotePropertySelectValue.objects.filter(
                sales_channel=self.sales_channel, local_instance=self.target
            ).count(),
            1,
        )
