from unittest.mock import patch

from django.db import transaction

from integrations.helpers import get_import_path
from integrations.models import IntegrationTaskQueue
from products.models import Product
from sales_channels.integrations.ebay.models import EbayProduct, EbaySalesChannelView
from sales_channels.integrations.ebay.tasks import (
    create_ebay_product_db_task,
    resync_ebay_product_db_task,
    update_ebay_assign_offers_db_task,
)
from sales_channels.integrations.ebay.tests.tests_factories.mixins import TestCaseEbayMixin
from sales_channels.models import SalesChannelViewAssign
from sales_channels.signals import (
    create_remote_product,
    manual_sync_remote_product,
    sales_view_assign_updated,
)


class EbayLiveReceiversTests(TestCaseEbayMixin):
    def setUp(self):
        super().setUp()
        self.view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="EBAY_GB",
            name="UK",
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = EbayProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        assign_patcher = patch(
            "sales_channels.signals.create_remote_product.send",
            return_value=[],
        )
        assign_patcher.start()
        try:
            self.assign = SalesChannelViewAssign.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=self.product,
                sales_channel=self.sales_channel,
                sales_channel_view=self.view,
                remote_product=self.remote_product,
            )
        finally:
            assign_patcher.stop()

    def test_ebay_manual_sync_queues_task(self):
        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            manual_sync_remote_product.send(
                sender=EbayProduct,
                instance=self.remote_product,
                view=self.view,
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
        self.assertEqual(task.task_name, get_import_path(resync_ebay_product_db_task))
        self.assertEqual(task.task_kwargs.get("product_id"), self.product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), self.remote_product.id)
        self.assertEqual(task.task_kwargs.get("view_id"), self.view.id)

    def test_ebay_create_from_assign_queues_task(self):
        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            create_remote_product.send(
                sender=SalesChannelViewAssign,
                instance=self.assign,
                view=self.view,
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
        self.assertEqual(task.task_name, get_import_path(create_ebay_product_db_task))
        self.assertEqual(task.task_kwargs.get("product_id"), self.product.id)
        self.assertEqual(task.task_kwargs.get("view_id"), self.view.id)

    def test_ebay_assign_update_queues_task(self):
        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            sales_view_assign_updated.send(
                sender=Product,
                instance=self.product,
                sales_channel=self.sales_channel,
                view=self.view,
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
        self.assertEqual(task.task_name, get_import_path(update_ebay_assign_offers_db_task))
        self.assertEqual(task.task_kwargs.get("product_id"), self.product.id)
        self.assertEqual(task.task_kwargs.get("view_id"), self.view.id)
