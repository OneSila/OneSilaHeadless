from django.core.exceptions import ValidationError
from django.db import IntegrityError
from model_bakery import baker

from core.tests import TestCase
from properties.models import Property, PropertySelectValue
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.integrations.amazon.models.properties import AmazonProperty
from sales_channels.integrations.ebay.models import EbaySalesChannel, EbaySalesChannelView
from sales_channels.integrations.ebay.models.properties import EbayProperty
from sales_channels.integrations.magento2.models import MagentoSalesChannel, MagentoProperty
from sales_channels.integrations.magento2.models.properties import MagentoPropertySelectValue
from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.integrations.shein.models.properties import SheinProperty, SheinPropertySelectValue
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
        self.shein_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.example.com",
        )
        self.ebay_channel = baker.make(
            EbaySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="ebay.example.com",
        )
        self.ebay_view = baker.make(
            EbaySalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.ebay_channel,
            remote_id="EBAY_GB",
            default_category_tree_id="0",
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

    def test_save_allows_type_change_from_int_to_float_when_rule_permits_it(self):
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

        remote_property.save()

        self.assertIsNotNone(remote_property.pk)

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

    def test_shein_save_forces_allow_multiple_true(self):
        remote_property = baker.make(
            SheinProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.shein_channel,
            remote_id="shein-color",
            allow_multiple=False,
        )

        remote_property.refresh_from_db()
        self.assertTrue(remote_property.allow_multiple)

    def test_ebay_save_forces_allow_multiple_true(self):
        remote_property = baker.make(
            EbayProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.ebay_channel,
            marketplace=self.ebay_view,
            localized_name="Brand",
            allow_multiple=False,
        )

        remote_property.refresh_from_db()
        self.assertTrue(remote_property.allow_multiple)

    def test_shein_select_value_save_inherits_allow_multiple_from_remote_property(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=local_property,
        )
        remote_property = baker.make(
            SheinProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.shein_channel,
            local_instance=local_property,
            remote_id="shein-color",
            type=Property.TYPES.SELECT,
            allow_multiple=False,
        )

        remote_value = baker.make(
            SheinPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.shein_channel,
            remote_property=remote_property,
            local_instance=local_value,
            remote_id="RED-A",
            value="Red",
            allow_multiple=False,
        )

        remote_value.refresh_from_db()
        self.assertTrue(remote_value.allow_multiple)

    def test_remote_select_value_unique_when_allow_multiple_false(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=local_property,
        )
        remote_property = baker.make(
            MagentoProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.magento_channel,
            local_instance=local_property,
            attribute_code="magento-color",
            allow_multiple=False,
        )

        baker.make(
            MagentoPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.magento_channel,
            remote_property=remote_property,
            local_instance=local_value,
            remote_id="1",
            allow_multiple=False,
        )

        with self.assertRaises(IntegrityError):
            MagentoPropertySelectValue.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.magento_channel,
                remote_property=remote_property,
                local_instance=local_value,
                remote_id="2",
                allow_multiple=False,
            )
