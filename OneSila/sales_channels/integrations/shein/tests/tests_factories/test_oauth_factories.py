"""Tests for Shein OAuth factories."""

from core.tests import TestCase
from model_bakery import baker

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
