"""Tests for Shein rule item synchronization."""

from core.tests import TestCase
from model_bakery import baker

from properties.models import ProductPropertiesRule, ProductPropertiesRuleItem, Property
from sales_channels.integrations.shein.factories.sync.rule_sync import (
    SheinPropertyRuleItemSyncFactory,
)
from sales_channels.integrations.shein.models import (
    SheinProductType,
    SheinProductTypeItem,
    SheinProperty,
    SheinSalesChannel,
)


class SheinRuleSyncTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_type_property = Property.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
            is_product_type=True,
        )
        product_type_value = baker.make(
            "properties.PropertySelectValue",
            multi_tenant_company=self.multi_tenant_company,
            property=product_type_property,
        )
        self.rule = ProductPropertiesRule.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            product_type=product_type_value,
        )
        self.property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        self.shein_property = baker.make(
            SheinProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.property,
        )
        self.product_type = baker.make(
            SheinProductType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.rule,
        )
        self.product_type_item = baker.make(
            SheinProductTypeItem,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type=self.product_type,
            property=self.shein_property,
            attribute_type=SheinProductTypeItem.AttributeType.SALES,
            requirement=SheinProductTypeItem.Requirement.OPTIONAL,
        )

    def test_sync_creates_optional_in_configurator_rule_item(self) -> None:
        SheinPropertyRuleItemSyncFactory(shein_property=self.shein_property).run()

        rule_item = ProductPropertiesRuleItem.objects.get(
            rule=self.rule,
            property=self.property,
        )
        self.assertEqual(
            rule_item.type,
            ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR,
        )
