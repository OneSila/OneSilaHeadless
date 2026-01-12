import base64
import hashlib
import hmac
import json
from unittest.mock import PropertyMock, patch

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from django.test import override_settings

from core.tests import TestCase
from model_bakery import baker

from integrations.models import IntegrationLog
from products.models import Product
from sales_channels.integrations.shein import constants
from sales_channels.integrations.shein.models import SheinSalesChannel, SheinProduct
from sales_channels.integrations.shein.factories.imports.product_refresh import (
    SheinProductDetailRefreshFactory,
)
from sales_channels.models.logs import RemoteLog
from sales_channels.models.products import RemoteProduct


@override_settings(SHEIN_APP_ID="app-id", SHEIN_APP_SECRET="app-secret-123456")
class SheinWebhookTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.test",
            remote_id="SC-1",
            open_key_id="open-key",
            secret_key="secret-key",
        )
        self.app_id = "app-id"
        self.app_secret = "app-secret-123456"
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            active=True,
            sku="SKU-1",
        )
        self.remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku=self.product.sku,
            spu_name="h23121539315"
        )
        self.webhook_path = "/direct/integrations/shein/webhooks"

    def _build_signature(self, *, path: str, timestamp: int, random_key: str) -> str:
        value = f"{self.app_id}&{timestamp}&{path}"
        secret_key = self.app_secret
        key = f"{secret_key}{random_key}"
        digest = hmac.new(key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).digest()
        hex_signature = digest.hex()
        base64_signature = base64.b64encode(hex_signature.encode("utf-8")).decode("utf-8")
        return f"{random_key}{base64_signature}"

    def _encrypt_event_data(self, payload: dict) -> str:
        raw = json.dumps(payload)
        key_bytes = self.app_secret.encode("utf-8")[:16]
        iv_bytes = constants.DEFAULT_AES_IV.encode("utf-8")[:16]
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        encrypted = cipher.encrypt(pad(raw.encode("utf-8"), AES.block_size))
        return base64.b64encode(encrypted).decode("utf-8")

    @patch.object(SheinProductDetailRefreshFactory, "run")
    def test_audit_webhook_resolves_remote_product_by_spu_name(self, refresh_mock) -> None:
        version = "SPMP231215009184753"
        document_sn = "SPMPA420231215003106"

        SheinProduct.objects.filter(pk=self.remote_product.pk).update(
            remote_id="h23121539315",
        )

        body = {
            "spu_name": "h23121539315",
            "skc_name": "sh2312153931579766",
            "sku_list": [{"sku_code": "I81ynllyzffh"}],
            "document_sn": document_sn,
            "version": version,
            "audit_time": "2023-12-18 11:46:43",
            "audit_state": 2,
            "failed_reason": None,
        }

        timestamp = 1700000000000
        random_key = "abc12"
        signature = self._build_signature(path=self.webhook_path, timestamp=timestamp, random_key=random_key)
        event_data = self._encrypt_event_data(body)

        response = self.client.post(
            self.webhook_path,
            data={"eventData": event_data},
            **{
                "HTTP_X_LT_OPENKEYID": self.sales_channel.open_key_id,
                "HTTP_X_LT_APPID": self.app_id,
                "HTTP_X_LT_TIMESTAMP": str(timestamp),
                "HTTP_X_LT_SIGNATURE": signature,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.remote_id, "h23121539315")
        refresh_mock.assert_not_called()

    @patch("sales_channels.models.products.RemoteProduct.errors", new_callable=PropertyMock)
    def test_audit_webhook_marks_approval_rejected_on_failure(self, errors_mock) -> None:
        errors_mock.return_value = IntegrationLog.objects.none()
        body = {
            "spu_name": "h23121539315",
            "skc_name": "sh2312153931579766",
            "sku_list": [{"sku_code": "I81ynllyzffh"}],
            "document_sn": "SPMPA420231215003106",
            "version": "SPMP231215009184753",
            "audit_time": "2023-12-18 11:46:43",
            "audit_state": 3,
            "failed_reason": ["Missing brand authorization"],
        }

        timestamp = 1700000000000
        random_key = "abc12"
        signature = self._build_signature(path=self.webhook_path, timestamp=timestamp, random_key=random_key)
        event_data = self._encrypt_event_data(body)

        response = self.client.post(
            self.webhook_path,
            data={"eventData": event_data},
            **{
                "HTTP_X_LT_OPENKEYID": self.sales_channel.open_key_id,
                "HTTP_X_LT_APPID": self.app_id,
                "HTTP_X_LT_TIMESTAMP": str(timestamp),
                "HTTP_X_LT_SIGNATURE": signature,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, RemoteProduct.STATUS_APPROVAL_REJECTED)

        log = RemoteLog.objects.filter(
            remote_product=self.remote_product,
            identifier="SheinProductAuditFailed",
            user_error=True,
        ).first()
        self.assertIsNotNone(log)
        self.assertIn("Missing brand authorization".lower(), (log.response or "").lower())

    @patch.object(SheinProductDetailRefreshFactory, "run")
    def test_audit_webhook_refreshes_details_on_completion(self, refresh_mock) -> None:
        self.remote_product.refresh_status(override_status=RemoteProduct.STATUS_PENDING_APPROVAL)

        body = {
            "spu_name": "h23121539315",
            "skc_name": "sh2312153931579766",
            "sku_list": [{"sku_code": "I81ynllyzffh"}],
            "document_sn": "SPMPA420231215003106",
            "version": "SPMP231215009184753",
            "audit_time": "2023-12-18 11:46:43",
            "audit_state": 2,
            "failed_reason": None,
        }

        timestamp = 1700000000000
        random_key = "abc12"
        signature = self._build_signature(path=self.webhook_path, timestamp=timestamp, random_key=random_key)
        event_data = self._encrypt_event_data(body)

        response = self.client.post(
            self.webhook_path,
            data={"eventData": event_data},
            **{
                "HTTP_X_LT_OPENKEYID": self.sales_channel.open_key_id,
                "HTTP_X_LT_APPID": self.app_id,
                "HTTP_X_LT_TIMESTAMP": str(timestamp),
                "HTTP_X_LT_SIGNATURE": signature,
            },
        )

        self.assertEqual(response.status_code, 200)
        refresh_mock.assert_called_once()
