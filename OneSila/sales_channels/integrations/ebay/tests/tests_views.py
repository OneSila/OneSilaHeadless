import hashlib
import hmac
import json

from django.test import Client, override_settings

from core.tests import TestCase
from sales_channels.integrations.ebay.models.sales_channels import EbaySalesChannel


class EbayMarketplaceAccountDeletionViewTests(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.url = "/direct/integrations/ebay/account-deletion/"

    @override_settings(EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN="A" * 40)
    def test_challenge_response_returns_expected_signature(self):
        challenge_code = "challenge-code"
        endpoint = "https://example.com/direct/integrations/ebay/account-deletion/"

        response = self.client.get(
            self.url,
            data={
                "challenge_code": challenge_code,
                "endpoint": endpoint,
                "verification_token": "A" * 40,
            },
        )

        expected_signature = hmac.new(
            key=("A" * 40).encode("utf-8"),
            msg=f"{challenge_code}{endpoint}".encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"challengeResponse": expected_signature})

    @override_settings(EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN="B" * 32)
    def test_notification_marks_sales_channel_for_deletion(self):
        channel = EbaySalesChannel.objects.create(
            hostname="ebay-store",
            multi_tenant_company=self.multi_tenant_company,
            remote_id="seller-123",
        )

        payload = {
            "notification": {
                "data": {
                    "sellerId": "seller-123",
                }
            }
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_EBAY_VERIFICATION_TOKEN="B" * 32,
        )

        self.assertEqual(response.status_code, 200)
        channel.refresh_from_db()
        self.assertTrue(channel.mark_for_delete)

    @override_settings(EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN="C" * 32)
    def test_notification_with_invalid_token_is_rejected(self):
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type="application/json",
            HTTP_X_EBAY_VERIFICATION_TOKEN="invalid-token",
        )

        self.assertEqual(response.status_code, 403)
