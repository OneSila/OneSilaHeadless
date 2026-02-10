from django.core.exceptions import ValidationError
from model_bakery import baker

from core.tests import TestCase
from properties.models import Property
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.integrations.amazon.models.properties import AmazonProperty
from sales_channels.integrations.magento2.models import MagentoSalesChannel, MagentoProperty
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel, WoocommerceGlobalAttribute
from sales_channels.tests.helpers import DisableMagentoAndWooConnectionsMixin


class RemotePropertySaveRulesTestCase(DisableMagentoAndWooConnectionsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.amazon_channel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="amazon.example.com",
        )
        self.magento_channel = baker.make(
            MagentoSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://magento.example.com",
        )
        self.woocommerce_channel = baker.make(
            WoocommerceSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://woo.example.com",
        )

    def test_magento_save_forces_original_type_and_type_from_local_instance(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.FLOAT,
        )

        remote_property = baker.make(
            MagentoProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.magento_channel,
            local_instance=local_property,
            attribute_code="weight",
            original_type=Property.TYPES.INT,
            type=Property.TYPES.TEXT,
        )

        remote_property.refresh_from_db()
        self.assertEqual(remote_property.original_type, Property.TYPES.FLOAT)
        self.assertEqual(remote_property.type, Property.TYPES.FLOAT)

    def test_woocommerce_save_forces_original_type_and_type_from_local_instance_on_each_save(self):
        first_local = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.INT,
        )
        second_local = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )

        remote_property = baker.make(
            WoocommerceGlobalAttribute,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.woocommerce_channel,
            local_instance=first_local,
            original_type=Property.TYPES.FLOAT,
            type=Property.TYPES.FLOAT,
        )
        self.assertEqual(remote_property.original_type, Property.TYPES.INT)
        self.assertEqual(remote_property.type, Property.TYPES.INT)

        remote_property.local_instance = second_local
        remote_property.save()
        remote_property.refresh_from_db()

        self.assertEqual(remote_property.original_type, Property.TYPES.TEXT)
        self.assertEqual(remote_property.type, Property.TYPES.TEXT)

    def test_save_raises_error_when_local_type_does_not_match_remote_type(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        remote_property = baker.prepare(
            AmazonProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.amazon_channel,
            code="material",
            local_instance=local_property,
            original_type=Property.TYPES.TEXT,
            type=Property.TYPES.INT,
        )

        with self.assertRaises(ValidationError):
            remote_property.save()

    def test_save_raises_error_when_original_type_cannot_change_to_target_type(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.FLOAT,
        )
        remote_property = baker.prepare(
            AmazonProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.amazon_channel,
            code="size",
            local_instance=local_property,
            original_type=Property.TYPES.INT,
            type=Property.TYPES.FLOAT,
        )

        with self.assertRaises(ValidationError):
            remote_property.save()

    def test_save_allows_type_change_when_rule_permits_it(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.INT,
        )

        remote_property = baker.make(
            AmazonProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.amazon_channel,
            code="quantity",
            local_instance=local_property,
            original_type=Property.TYPES.FLOAT,
            type=Property.TYPES.INT,
        )

        self.assertIsNotNone(remote_property.pk)

    def test_select_without_custom_values_disallows_int_target(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.INT,
        )
        remote_property = baker.prepare(
            AmazonProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.amazon_channel,
            code="color",
            local_instance=local_property,
            original_type=Property.TYPES.SELECT,
            allows_unmapped_values=False,
            type=Property.TYPES.INT,
        )

        with self.assertRaises(ValidationError):
            remote_property.save()

    def test_select_with_custom_values_allows_int_target(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.INT,
        )

        remote_property = baker.make(
            AmazonProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.amazon_channel,
            code="color",
            local_instance=local_property,
            original_type=Property.TYPES.SELECT,
            allows_unmapped_values=True,
            type=Property.TYPES.INT,
        )

        self.assertIsNotNone(remote_property.pk)
