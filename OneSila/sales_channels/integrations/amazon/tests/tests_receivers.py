from unittest.mock import patch

from core.tests import TestCase
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonProduct,
)
from sales_channels.integrations.amazon.models.properties import AmazonProductType
from products.models import Product
from sales_channels.signals import manual_sync_remote_product
from sales_channels.integrations.amazon.tasks import resync_amazon_product_db_task
from .helpers import DisableWooCommerceSignalsMixin


class AmazonProductTypeReceiversTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )

    @patch("sales_channels.integrations.amazon.receivers.create_amazon_product_type_rule_task")
    def test_factory_run_triggered_on_imported_change(self, task_func):
        pt = AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type_code="CHAIR",
            imported=False,
        )

        pt.imported = True
        pt.save()

        task_func.assert_called_once_with(
            product_type_code=pt.product_type_code,
            sales_channel_id=pt.sales_channel_id,
        )


class AmazonManualSyncReceiverTest(DisableWooCommerceSignalsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="VIEW",
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )

    # @patch("sales_channels.integrations.amazon.receivers.run_single_amazon_product_task_flow")
    # def test_manual_sync_queues_task(self, flow_mock):
    #     manual_sync_remote_product.send(
    #         sender=AmazonProduct,
    #         instance=self.remote_product,
    #         view=self.view,
    #         force_validation_only=True,
    #     )
    #
    #     flow_mock.assert_called_once()
    #     _, kwargs = flow_mock.call_args
    #     self.assertEqual(kwargs["task_func"], resync_amazon_product_db_task)
    #     self.assertTrue(kwargs["force_validation_only"])
    #     self.assertEqual(kwargs["view"], self.view)
