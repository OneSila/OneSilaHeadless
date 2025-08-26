from core.tests import TestCase
from django.core.exceptions import ValidationError
from model_bakery import baker
from unittest.mock import patch

from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonProductBrowseNode,
    AmazonVariationTheme,
)
from sales_channels.integrations.amazon.models.properties import AmazonProperty
from sales_channels.integrations.amazon.tests.helpers import DisableWooCommerceSignalsMixin
from sales_channels.models import SalesChannelViewAssign
from properties.models import Property


class AmazonPropertyModelTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )

    # @TODO: Come back to this
    # def test_save_raises_error_for_type_mismatch(self):
    #     local_property = baker.make(Property, type=Property.TYPES.SELECT)
    #     amazon_property = baker.prepare(
    #         AmazonProperty,
    #         sales_channel=self.sales_channel,
    #         type=Property.TYPES.TEXT,
    #         local_instance=local_property,
    #     )
    #     with self.assertRaises(ValidationError):
    #         amazon_property.save()

    def test_save_allowed_when_types_match(self):
        local_property = baker.make(Property, type=Property.TYPES.SELECT)
        amazon_property = baker.make(
            AmazonProperty,
            sales_channel=self.sales_channel,
            type=Property.TYPES.SELECT,
            local_instance=local_property,
        )
        self.assertIsNotNone(amazon_property.pk)


class SalesChannelViewAssignValidationTest(DisableWooCommerceSignalsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )
        self.view = AmazonSalesChannelView.objects.create(
            sales_channel=self.channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.simple_product = baker.make(
            "products.Product",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.config_product = baker.make(
            "products.Product",
            type="CONFIGURABLE",
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_first_assign_requires_browse_node(self):
        with self.assertRaises(ValidationError):
            SalesChannelViewAssign.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=self.simple_product,
                sales_channel_view=self.view,
                sales_channel=self.channel,
            )

    def test_configurable_requires_variation_theme(self):
        AmazonProductBrowseNode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.config_product,
            sales_channel=self.channel,
            view=self.view,
            recommended_browse_node_id="1",
        )
        with self.assertRaises(ValidationError):
            SalesChannelViewAssign.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=self.config_product,
                sales_channel_view=self.view,
                sales_channel=self.channel,
            )

        with patch(
            "sales_channels.integrations.amazon.models.products.AmazonVariationTheme.full_clean",
            lambda self: None,
        ):
            AmazonVariationTheme.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=self.config_product,
                view=self.view,
                theme="Size/Color",
            )
            assign = SalesChannelViewAssign.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=self.config_product,
                sales_channel_view=self.view,
                sales_channel=self.channel,
            )
            self.assertIsNotNone(assign.pk)

