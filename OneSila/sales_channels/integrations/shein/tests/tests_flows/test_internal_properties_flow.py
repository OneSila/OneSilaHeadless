"""Tests for the Shein internal property flow."""

from unittest.mock import Mock, patch

from core.tests import TestCase
from model_bakery import baker

from sales_channels.integrations.shein import constants
from sales_channels.integrations.shein.flows.internal_properties import (
    SheinInternalPropertiesFlow,
    ensure_internal_properties_flow,
)
from sales_channels.integrations.shein.models import (
    SheinInternalProperty,
    SheinInternalPropertyOption,
    SheinSalesChannel,
)


BRAND_LIST_RESPONSE = {
    "code": "0",
    "msg": "OK",
    "info": {
        "data": [
            {"brand_code": "abc123", "brand_name": "First Brand"},
            {"brand_code": "def456", "brand_name": "Second Brand"},
        ]
    },
}


class SheinInternalPropertiesFlowTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            open_key_id="open-key",
            secret_key="secret-key",
        )

    def test_flow_creates_internal_properties_and_brand_options(self) -> None:
        response = Mock()
        response.json.return_value = BRAND_LIST_RESPONSE

        with patch.object(SheinInternalPropertiesFlow, "shein_post", return_value=response) as mock_post:
            ensure_internal_properties_flow(self.sales_channel)

        self.assertTrue(mock_post.called)
        properties = SheinInternalProperty.objects.filter(sales_channel=self.sales_channel)
        self.assertEqual(properties.count(), len(constants.SHEIN_INTERNAL_PROPERTY_DEFINITIONS))

        brand_property = properties.get(code="brand_code")
        options = SheinInternalPropertyOption.objects.filter(internal_property=brand_property)
        self.assertEqual(options.count(), 2)
        values = set(options.values_list("value", flat=True))
        self.assertEqual(values, {"abc123", "def456"})
        self.assertTrue(options.filter(label="First Brand", is_active=True).exists())

        package_property = properties.get(code="package_type")
        package_options = SheinInternalPropertyOption.objects.filter(internal_property=package_property, is_active=True)
        self.assertEqual(package_options.count(), 5)
        self.assertTrue(package_options.filter(value="0", label="Clear packaging").exists())

    def test_flow_gracefully_handles_missing_credentials(self) -> None:
        with patch.object(SheinInternalPropertiesFlow, "shein_post", side_effect=ValueError):
            ensure_internal_properties_flow(self.sales_channel)

        properties = SheinInternalProperty.objects.filter(sales_channel=self.sales_channel)
        # Internal definitions are still created even if the brand call fails.
        self.assertEqual(properties.count(), len(constants.SHEIN_INTERNAL_PROPERTY_DEFINITIONS))
        self.assertFalse(SheinInternalPropertyOption.objects.filter(sales_channel=self.sales_channel, value="abc123").exists())
        self.assertTrue(
            SheinInternalPropertyOption.objects.filter(
                sales_channel=self.sales_channel,
                internal_property__code="package_type",
                is_active=True,
            ).exists()
        )
