from unittest.mock import patch

from django.db import transaction

from core.tests import TestCase
from integrations.helpers import get_import_path
from integrations.models import IntegrationTaskQueue
from products.models import Product
from sales_channels.integrations.mirakl.models import (
    MiraklProduct,
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
    MiraklSalesChannelView,
)
from sales_channels.integrations.mirakl.tasks import (
    create_mirakl_product_db_task,
    delete_mirakl_product_db_task,
    process_mirakl_feed_db_task,
    resync_mirakl_product_db_task,
)
from sales_channels.models import SalesChannelViewAssign
from sales_channels.signals import create_remote_product, delete_remote_product, manual_sync_remote_product
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


def _noop_dispatch_task(self, *, _unused=None):
    return None


class MiraklLiveReceiversTests(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = MiraklSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = MiraklProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        self.view = MiraklSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="DEFAULT",
            name="Default",
        )

    def test_mirakl_manual_sync_queues_task(self):
        with patch(
            "sales_channels.factories.task_queue.task_queue.add_task_to_queue",
        ) as add_task_mock, patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            manual_sync_remote_product.send(
                sender=MiraklProduct,
                instance=self.remote_product,
                view=self.view,
            )

        add_task_mock.assert_called_once_with(
            integration_id=self.sales_channel.id,
            task_func_path=get_import_path(resync_mirakl_product_db_task),
            task_kwargs={
                "sales_channel_id": self.sales_channel.id,
                "view_id": self.view.id,
                "product_id": self.product.id,
                "remote_product_id": self.remote_product.id,
            },
            number_of_remote_requests=1,
        )

    def test_mirakl_create_from_assign_queues_task(self):
        assign = SalesChannelViewAssign.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            multi_tenant_company=self.multi_tenant_company,
        )

        with patch(
            "sales_channels.factories.task_queue.task_queue.add_task_to_queue",
        ) as add_task_mock, patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            create_remote_product.send(
                sender=SalesChannelViewAssign,
                instance=assign,
                view=self.view,
            )

        add_task_mock.assert_called_once_with(
            integration_id=self.sales_channel.id,
            task_func_path=get_import_path(create_mirakl_product_db_task),
            task_kwargs={
                "sales_channel_id": self.sales_channel.id,
                "view_id": self.view.id,
                "product_id": self.product.id,
            },
            number_of_remote_requests=1,
        )

    def test_mirakl_product_delete_from_assign_queues_task(self):
        assign = SalesChannelViewAssign.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
            multi_tenant_company=self.multi_tenant_company,
        )

        with patch(
            "sales_channels.factories.task_queue.task_queue.add_task_to_queue",
        ) as add_task_mock, patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            delete_remote_product.send(
                sender=SalesChannelViewAssign,
                instance=assign,
            )

        add_task_mock.assert_called_once_with(
            integration_id=self.sales_channel.id,
            task_func_path=get_import_path(delete_mirakl_product_db_task),
            task_kwargs={
                "sales_channel_id": self.sales_channel.id,
                "view_id": self.view.id,
                "product_id": self.product.id,
                "remote_product_id": self.remote_product.id,
            },
            number_of_remote_requests=1,
        )

    @patch(
        "integrations.factories.task_queue.TaskQueueFactory.dispatch_task",
        new=_noop_dispatch_task,
    )
    def test_feed_status_change_to_ready_to_render_queues_processing_task(self, *, _unused=None):
        feed = MiraklSalesChannelFeed.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelFeed.TYPE_COMBINED,
            stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_GATHERING_PRODUCTS,
        )

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            feed.status = MiraklSalesChannelFeed.STATUS_READY_TO_RENDER
            feed.save(update_fields=["status", "updated_at"])

        task = IntegrationTaskQueue.objects.get(task_name=get_import_path(process_mirakl_feed_db_task))
        self.assertEqual(task.integration_id, self.sales_channel.id)
        self.assertEqual(
            task.task_kwargs,
            {
                "feed_id": feed.id,
                "sales_channel_id": self.sales_channel.id,
            },
        )
