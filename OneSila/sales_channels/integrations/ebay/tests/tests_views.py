import hashlib
import json

from django.test import Client, override_settings
from django.urls import reverse

from core.tests import TestCase
from sales_channels.integrations.ebay.models.sales_channels import EbaySalesChannel


class EbayMarketplaceAccountDeletionViewTests(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.url = reverse("ebay:marketplace_account_deletion")

    @override_settings(
        EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN="A" * 40,
        EBAY_ACCOUNT_DELETION_ENDPOINT="https://example.com/direct/integrations/ebay/account-deletion",
    )
    def test_challenge_response_returns_expected_signature(self):
        challenge_code = "challenge-code"
        endpoint = "https://example.com/direct/integrations/ebay/account-deletion"

        response = self.client.get(
            self.url,
            data={
                "challenge_code": challenge_code,
                "verification_token": "A" * 40,
            },
        )

        expected_signature = hashlib.sha256(
            f"{challenge_code}{'A' * 40}{endpoint}".encode("utf-8")
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
    def test_notification_with_invalid_token_returns_200(self):
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type="application/json",
            HTTP_X_EBAY_VERIFICATION_TOKEN="invalid-token",
        )

        self.assertEqual(response.status_code, 200)
