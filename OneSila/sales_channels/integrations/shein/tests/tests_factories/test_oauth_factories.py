"""Tests for Shein OAuth factories."""

from django.core.exceptions import ValidationError
from django.test import override_settings
from core.tests import TestCase
from model_bakery import baker
from unittest.mock import patch

from sales_channels.integrations.shein.factories.sales_channels.oauth import ValidateSheinAuthFactory
from sales_channels.integrations.shein.models import SheinSalesChannel


class SheinOAuthPersistTests(TestCase):
    def test_persist_does_not_override_remote_id(self):
        baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="4489837",
        )
        sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="keep-me",
        )
        factory = ValidateSheinAuthFactory(
            sales_channel=sales_channel,
            app_id="app-id",
            temp_token="temp-token",
        )
        factory.decrypted_secret = "secret"

        payload = {
            "state": "state-1",
            "openKeyId": "OPEN-1",
            "secretKey": "encrypted",
            "supplierId": "4489837",
            "supplierSource": "10",
            "supplierBusinessMode": "B2C",
        }

        factory._persist(payload)

        sales_channel.refresh_from_db()
        self.assertEqual(sales_channel.remote_id, "keep-me")
        self.assertEqual(sales_channel.open_key_id, "OPEN-1")
        self.assertEqual(sales_channel.supplier_id, 4489837)

    @override_settings(SHEIN_APP_ID="app-id")
    @patch(
        "sales_channels.integrations.shein.factories.sales_channels.oauth"
        ".ValidateSheinAuthFactory._call_token_endpoint"
    )
    def test_run_raises_when_open_key_already_connected(self, mock_call_token):
        existing_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            open_key_id="OPEN-1",
            hostname="existing-host",
        )
        sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="new-host",
        )
        mock_call_token.return_value = {"openKeyId": "OPEN-1", "secretKey": "encrypted"}

        factory = ValidateSheinAuthFactory(
            sales_channel=sales_channel,
            app_id="app-id",
            temp_token="temp-token",
        )

        with self.assertRaises(ValidationError) as exc:
            factory.run()

        self.assertIn(existing_channel.hostname, exc.exception.message_dict["__all__"][0])
