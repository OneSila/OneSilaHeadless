import base64
import hashlib
import hmac
import json

from core.tests import TestCase
from model_bakery import baker

from products.models import Product
from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.models.products import RemoteProduct


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
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            active=True,
            sku="SKU-1",
        )
        self.remote_product = RemoteProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku=self.product.sku,
        )
        self.webhook_path = "/direct/integrations/shein/product_document_audit_status_notice"

    def _build_signature(self, *, path: str, timestamp: int, random_key: str) -> str:
        open_key_id = self.sales_channel.open_key_id
        secret_key = self.sales_channel.secret_key
        value = f"{open_key_id}&{timestamp}&{path}"
        key = f"{secret_key}{random_key}"
        digest = hmac.new(key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).digest()
        hex_signature = digest.hex()
        base64_signature = base64.b64encode(hex_signature.encode("utf-8")).decode("utf-8")
        return f"{random_key}{base64_signature}"

    def test_audit_webhook_updates_remote_id_by_version(self) -> None:
        version = "SPMP231215009184753"
        document_sn = "SPMPA420231215003106"

        self.remote_product.add_log(
            action="CREATE",
            response={"version": version, "document_sn": document_sn},
            payload={"version": version, "document_sn": document_sn},
            identifier="SheinProductSubmission",
            remote_product=self.remote_product,
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

        response = self.client.post(
            self.webhook_path,
            data=json.dumps(body),
            content_type="application/json",
            **{
                "HTTP_X_LT_OPENKEYID": self.sales_channel.open_key_id,
                "HTTP_X_LT_TIMESTAMP": str(timestamp),
                "HTTP_X_LT_SIGNATURE": signature,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.remote_id, "h23121539315")

