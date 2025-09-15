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