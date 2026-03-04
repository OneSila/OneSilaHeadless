from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker

from sales_channels.integrations.shein.exceptions import SheinResponseException
from sales_channels.integrations.shein.factories.products import SheinProductDeleteFactory
from sales_channels.integrations.shein.models import SheinProduct, SheinSalesChannel


class _FakeResponse:
    def __init__(self, *, payload):
        self._payload = payload

    def json(self):
        return self._payload


class SheinProductDeleteFactoryTests(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            open_key_id="open-key",
            secret_key="secret-key",
            active=True,
        )
        self.local_product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.local_product,
            remote_id="s2502064450",
        )

    def _build_factory(self):
        return SheinProductDeleteFactory(
            sales_channel=self.sales_channel,
            remote_instance=self.remote_product,
        )

    @patch("sales_channels.integrations.shein.factories.products.products.SheinProductDeleteFactory.shein_post")
    def test_delete_remote_returns_payload_on_full_success(self, shein_post_mock):
        shein_post_mock.return_value = _FakeResponse(
            payload={
                "code": "0",
                "msg": "OK",
                "info": {
                    "successList": [{"documentSn": "SPMPA420250211000105", "skcName": "ss25021193534484"}],
                    "failList": [],
                    "total": 1,
                    "successCount": 1,
                    "failCount": 0,
                },
            }
        )

        payload = self._build_factory().delete_remote()

        self.assertEqual(payload.get("code"), "0")
        shein_post_mock.assert_called_once_with(
            path="/open-api/goods/revoke-product",
            payload={"spuName": "s2502064450"},
        )

    @patch("sales_channels.integrations.shein.factories.products.products.SheinProductDeleteFactory.shein_post")
    def test_delete_remote_raises_on_non_zero_code(self, shein_post_mock):
        shein_post_mock.return_value = _FakeResponse(
            payload={
                "code": "1001",
                "msg": "Invalid status",
                "info": {},
            }
        )

        with self.assertRaises(SheinResponseException):
            self._build_factory().delete_remote()

    @patch("sales_channels.integrations.shein.factories.products.products.SheinProductDeleteFactory.shein_post")
    def test_delete_remote_raises_on_fail_list(self, shein_post_mock):
        shein_post_mock.return_value = _FakeResponse(
            payload={
                "code": "0",
                "msg": "OK",
                "info": {
                    "successList": [],
                    "failList": [
                        {
                            "documentSn": "SPMPA420250211000104",
                            "skcName": "ss25021193538318",
                            "msg": "Product already approved",
                        }
                    ],
                    "total": 1,
                    "successCount": 0,
                    "failCount": 1,
                },
            }
        )

        with self.assertRaises(SheinResponseException):
            self._build_factory().delete_remote()
