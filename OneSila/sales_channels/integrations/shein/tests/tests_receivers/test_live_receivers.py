from unittest.mock import patch

from django.db import transaction

from core.tests import TestCase
from integrations.helpers import get_import_path
from integrations.models import IntegrationTaskQueue
from products.models import Product
from sales_channels.integrations.shein.models import SheinProduct, SheinSalesChannel
from sales_channels.integrations.shein.tasks import resync_shein_product_db_task
from sales_channels.signals import manual_sync_remote_product


class SheinLiveReceiversTests(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = SheinProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )

    def test_shein_manual_sync_queues_task(self, *, _unused=None):
        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            manual_sync_remote_product.send(
                sender=SheinProduct,
                instance=self.remote_product,
            )

        self.assertEqual(
            IntegrationTaskQueue.objects.filter(
                integration_id=self.sales_channel.id,
            ).count(),
            initial_count + 1,
        )
        task = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).latest("id")
        self.assertEqual(task.task_name, get_import_path(resync_shein_product_db_task))
        self.assertEqual(task.task_kwargs.get("sales_channel_id"), self.sales_channel.id)
        self.assertEqual(task.task_kwargs.get("product_id"), self.product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), self.remote_product.id)
