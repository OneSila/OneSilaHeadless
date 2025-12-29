from unittest.mock import PropertyMock, patch

from model_bakery import baker

from core.tests import TestCase
from integrations.models import IntegrationLog
from products.models import Product
from sales_channels.integrations.shein.factories.products.document_state import (
    SheinProductDocumentStateFactory,
)
from sales_channels.integrations.shein.models import SheinSalesChannel, SheinProduct
from sales_channels.models.logs import RemoteLog
from sales_channels.models.products import RemoteProduct


class SheinDocumentStateFactoryTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.test",
            remote_id="SC-1",
        )
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
            spu_name="SPU-1",
            syncing_current_percentage=100,
        )

    @patch("sales_channels.models.products.RemoteProduct.errors", new_callable=PropertyMock)
    @patch.object(SheinProductDocumentStateFactory, "fetch")
    def test_review_failures_mark_approval_rejected(self, fetch_mock, errors_mock) -> None:
        errors_mock.return_value = IntegrationLog.objects.none()
        fetch_mock.return_value = {
            "info": {
                "data": [
                    {
                        "spuName": "SPU-1",
                        "version": "V1",
                        "skcList": [
                            {
                                "skcName": "SKC-1",
                                "documentState": 3,
                                "documentSn": "DOC-1",
                                "failedReason": ["Brand issue"],
                            }
                        ],
                    }
                ]
            }
        }

        factory = SheinProductDocumentStateFactory(
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )
        factory.run()

        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, RemoteProduct.STATUS_APPROVAL_REJECTED)

        log = RemoteLog.objects.filter(
            remote_product=self.remote_product,
            identifier="SheinProductDocumentState:review_failed",
            user_error=True,
        ).first()
        self.assertIsNotNone(log)
        self.assertIn("brand issue", (log.response or "").lower())
