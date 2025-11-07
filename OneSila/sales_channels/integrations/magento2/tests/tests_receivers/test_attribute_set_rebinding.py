from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker

from properties.models import (
    ProductPropertiesRuleItem,
    Property,
    PropertySelectValue,
)
from sales_channels.helpers import rebind_magento_attribute_sets_for_rule
from sales_channels.integrations.magento2.models.properties import (
    MagentoAttributeSetAttribute,
)
from sales_channels.integrations.magento2.receivers import (
    sales_channels__magento__attribute_set__create,
)


class MagentoAttributeSetRebindTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.product_type_property = baker.make(
            Property,
            is_product_type=True,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product_type_value = baker.make(
            PropertySelectValue,
            property=self.product_type_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.attribute_property = baker.make(
            Property,
            is_product_type=False,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.magento_channel = baker.make(
            'sales_channels.integrations.magento2.MagentoSalesChannel',
            multi_tenant_company=self.multi_tenant_company,
        )
        self.default_rule = baker.make(
            'properties.ProductPropertiesRule',
            product_type=self.product_type_value,
            sales_channel=None,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.channel_rule = baker.make(
            'properties.ProductPropertiesRule',
            product_type=self.product_type_value,
            sales_channel=self.magento_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.default_item = baker.make(
            ProductPropertiesRuleItem,
            rule=self.default_rule,
            property=self.attribute_property,
            type=ProductPropertiesRuleItem.REQUIRED,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.channel_item = baker.make(
            ProductPropertiesRuleItem,
            rule=self.channel_rule,
            property=self.attribute_property,
            type=ProductPropertiesRuleItem.REQUIRED,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.attribute_set = baker.make(
            'sales_channels.integrations.magento2.MagentoAttributeSet',
            local_instance=self.default_rule,
            sales_channel=self.magento_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_property = baker.make(
            'sales_channels.integrations.magento2.MagentoProperty',
            local_instance=self.attribute_property,
            sales_channel=self.magento_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        baker.make(
            'sales_channels.integrations.magento2.MagentoAttributeSetAttribute',
            magento_rule=self.attribute_set,
            local_instance=self.default_item,
            remote_property=self.remote_property,
            sales_channel=self.magento_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_rebind_magento_attribute_sets_for_rule_updates_associations(self):
        rebind_magento_attribute_sets_for_rule(rule=self.channel_rule)

        self.attribute_set.refresh_from_db()
        self.assertEqual(self.attribute_set.local_instance_id, self.channel_rule.id)

        attributes = MagentoAttributeSetAttribute.objects.filter(
            magento_rule=self.attribute_set,
        )
        self.assertEqual(attributes.count(), 1)
        self.assertEqual(
            attributes.first().local_instance_id,
            self.channel_item.id,
        )


class MagentoAttributeSetReceiverTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.product_type_property = baker.make(
            Property,
            is_product_type=True,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product_type_value = baker.make(
            PropertySelectValue,
            property=self.product_type_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.magento_channel = baker.make(
            'sales_channels.integrations.magento2.MagentoSalesChannel',
            multi_tenant_company=self.multi_tenant_company,
        )

    def _make_rule(self, *, sales_channel=None):
        return baker.make(
            'properties.ProductPropertiesRule',
            product_type=self.product_type_value,
            sales_channel=sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

    @patch('sales_channels.integrations.magento2.receivers.rebind_magento_attribute_sets_for_rule')
    @patch('sales_channels.integrations.magento2.receivers.run_generic_sales_channel_task_flow')
    def test_create_receiver_triggers_remote_task_for_default_rule(self, run_generic_mock, rebind_mock):
        rule = self._make_rule()

        sales_channels__magento__attribute_set__create(sender=None, instance=rule)

        run_generic_mock.assert_called_once()
        rebind_mock.assert_not_called()

    @patch('sales_channels.integrations.magento2.receivers.run_generic_sales_channel_task_flow')
    @patch('sales_channels.integrations.magento2.receivers.rebind_magento_attribute_sets_for_rule')
    def test_create_receiver_rebinds_for_channel_specific_rule(self, rebind_mock, run_generic_mock):
        rule = self._make_rule(sales_channel=self.magento_channel)

        sales_channels__magento__attribute_set__create(sender=None, instance=rule)

        rebind_mock.assert_called_once_with(rule=rule)
        run_generic_mock.assert_not_called()
