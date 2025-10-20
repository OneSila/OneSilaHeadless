from model_bakery import baker

from properties.models import Property, PropertySelectValue, ProductPropertiesRule
from sales_channels.integrations.ebay.models.properties import EbayProductType
from sales_channels.integrations.ebay.models.sales_channels import EbaySalesChannelView
from sales_channels.integrations.ebay.tests.tests_factories.mixins import (
    TestCaseEbayMixin,
)


class TestEbayProductTypeRuleTask(TestCaseEbayMixin):
    def setUp(self):
        super().setUp()

        self.view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="UK",
            remote_id="EBAY_GB",
            default_category_tree_id="0",
        )

        product_type_property = Property.objects.get(
            is_product_type=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_type_value = baker.make(
            PropertySelectValue,
            property=product_type_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product_rule = ProductPropertiesRule.objects.get(
            product_type=product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_task_triggered_when_local_instance_is_set(self):
        product_type = EbayProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            remote_id="123",
        )

        self.ebay_product_type_rule_sync_task.reset_mock()

        product_type.local_instance = self.product_rule
        product_type.save()

        self.ebay_product_type_rule_sync_task.assert_called_once_with(
            product_type_id=product_type.id,
        )

    def test_task_triggered_when_remote_id_is_set(self):
        product_type = EbayProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=self.product_rule,
        )

        self.ebay_product_type_rule_sync_task.reset_mock()

        product_type.remote_id = "987"
        product_type.save()

        self.ebay_product_type_rule_sync_task.assert_called_once_with(
            product_type_id=product_type.id,
        )

    def test_task_not_triggered_when_remote_id_is_blank(self):
        product_type = EbayProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=self.product_rule,
            remote_id="123",
        )

        self.ebay_product_type_rule_sync_task.reset_mock()

        product_type.remote_id = "   "
        product_type.save()

        self.ebay_product_type_rule_sync_task.assert_not_called()
