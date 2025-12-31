from unittest.mock import MagicMock, patch

from core.tests import TestCase
from model_bakery import baker

from products.models import Product
from sales_channels.exceptions import SkipSyncBecauseOfStatusException
from sales_channels.integrations.shein.factories.products import SheinProductUpdateFactory
from sales_channels.integrations.shein.models import SheinProduct, SheinSalesChannel
from sales_channels.models.logs import RemoteLog
from sales_channels.models.products import RemoteProduct


class SheinPendingApprovalSkipTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.test",
            remote_id="SC-1",
            starting_stock=5,
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
            remote_id="SPU-1",
            remote_sku="SKU-1",
            spu_name="SPU-1",
            syncing_current_percentage=100,
        )

    @patch.object(SheinProductUpdateFactory, "finalize_progress")
    def test_update_skips_pending_approval_and_logs_user_error(self, _finalize_progress) -> None:
        self.assertEqual(self.remote_product.status, RemoteProduct.STATUS_PENDING_APPROVAL)
        factory = SheinProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            get_value_only=True,
            skip_checks=True,
        )

        factory.run()

        log = RemoteLog.objects.filter(
            remote_product=self.remote_product,
            user_error=True,
            action=RemoteLog.ACTION_UPDATE,
        ).first()
        self.assertIsNotNone(log)
        self.assertIn("pending approval", (log.response or "").lower())

    def test_skip_exception_is_registered_as_user_exception(self) -> None:
        self.assertIn(SkipSyncBecauseOfStatusException, self.sales_channel._meta.user_exceptions)

    @patch.object(SheinProductUpdateFactory, "shein_post")
    def test_update_blocks_when_edit_permission_denied(self, shein_post: MagicMock) -> None:
        SheinProduct.objects.filter(pk=self.remote_product.pk).update(
            status=RemoteProduct.STATUS_COMPLETED,
        )
        self.remote_product.refresh_from_db()

        response = MagicMock()
        response.json.return_value = {
            "code": "0",
            "msg": "OK",
            "info": {"editable": False, "reason": "Review in progress."},
        }
        shein_post.return_value = response

        factory = SheinProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
        )

        with self.assertRaises(SkipSyncBecauseOfStatusException) as exc:
            factory.check_status(remote_product=self.remote_product)

        self.assertIn("Review in progress", str(exc.exception))
