from unittest.mock import patch

from model_bakery import baker

from properties.models import Property, PropertySelectValue, ProductPropertiesRule
from sales_channels.integrations.ebay.flows.product_type_rules import (
    EbayProductTypeRuleSyncFlow,
)
from sales_channels.integrations.ebay.models.properties import EbayProductType
from sales_channels.integrations.ebay.models.sales_channels import (
    EbayRemoteLanguage,
    EbaySalesChannelView,
)
from sales_channels.integrations.ebay.tests.tests_factories.mixins import (
    TestCaseEbayMixin,
)


class EbayProductTypeRuleSyncFlowTestCase(TestCaseEbayMixin):
    def setUp(self):
        super().setUp()

        self.view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="UK",
            remote_id="EBAY_GB",
            default_category_tree_id="0",
        )
        self.remote_language = EbayRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            local_instance="en-us",
            remote_code="en_US",
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
        self.product_rule, _ = ProductPropertiesRule.objects.get_or_create(
            product_type=product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.product_type = EbayProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            remote_id="123",
            local_instance=self.product_rule,
        )

    def test_flow_runs_factory_when_prerequisites_met(self):
        flow = EbayProductTypeRuleSyncFlow(product_type_id=self.product_type.id)

        with patch(
            "sales_channels.integrations.ebay.flows.product_type_rules.EbayProductTypeRuleFactory"
        ) as mock_factory:
            flow.work()

        mock_factory.assert_called_once_with(
            sales_channel=self.sales_channel,
            view=self.view,
            category_id="123",
            category_tree_id=self.view.default_category_tree_id,
            language=self.remote_language.local_instance,
        )
        mock_factory.return_value.run.assert_called_once_with()

    def test_flow_falls_back_to_company_language_when_remote_language_missing(self):
        self.view.remote_languages.all().delete()

        flow = EbayProductTypeRuleSyncFlow(product_type_id=self.product_type.id)

        with patch(
            "sales_channels.integrations.ebay.flows.product_type_rules.EbayProductTypeRuleFactory"
        ) as mock_factory:
            flow.work()

        mock_factory.assert_called_once_with(
            sales_channel=self.sales_channel,
            view=self.view,
            category_id="123",
            category_tree_id=self.view.default_category_tree_id,
            language=self.multi_tenant_company.language,
        )
        mock_factory.return_value.run.assert_called_once_with()

    def test_flow_skips_when_remote_id_missing(self):
        self.product_type.remote_id = None
        self.product_type.save()

        flow = EbayProductTypeRuleSyncFlow(product_type_id=self.product_type.id)

        with patch(
            "sales_channels.integrations.ebay.flows.product_type_rules.EbayProductTypeRuleFactory"
        ) as mock_factory:
            flow.work()

        mock_factory.assert_not_called()

    def test_flow_skips_when_local_rule_missing(self):
        self.product_type.local_instance = None
        self.product_type.save()

        flow = EbayProductTypeRuleSyncFlow(product_type_id=self.product_type.id)

        with patch(
            "sales_channels.integrations.ebay.flows.product_type_rules.EbayProductTypeRuleFactory"
        ) as mock_factory:
            flow.work()

        mock_factory.assert_not_called()
