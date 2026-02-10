from __future__ import annotations

from unittest.mock import patch

from model_bakery import baker
from django.db import transaction

from products.models import Product
from sales_channels.integrations.ebay import receivers as ebay_receivers
from integrations.helpers import get_import_path
from integrations.models import IntegrationTaskQueue
from sales_channels.integrations.ebay.models import EbayProduct
from sales_channels.integrations.ebay.models.sales_channels import EbaySalesChannelView
from sales_channels.integrations.ebay.tests.tests_factories.mixins import TestCaseEbayMixin
from sales_channels.models import SalesChannelViewAssign


class EbayDeleteReceiversTests(TestCaseEbayMixin):
    def setUp(self) -> None:
        super().setUp()
        self.view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="UK",
            remote_id="EBAY_GB",
        )
        type(self.view).objects.filter(pk=self.view.pk).update(
            fulfillment_policy_id="FULFILL-1",
            payment_policy_id="PAY-1",
            return_policy_id="RETURN-1",
            merchant_location_key="LOC-1",
        )
        self.view.refresh_from_db()
        self.product = baker.make(
            "products.Product",
            sku="SKU-1",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_product = EbayProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="SKU-1",
            remote_id="SKU-1",
        )
        self.assign = SalesChannelViewAssign.objects.create(
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
            multi_tenant_company=self.multi_tenant_company,
        )

    def tearDown(self) -> None:
        ebay_receivers._PENDING_PRODUCT_DELETE_COUNTS.clear()
        super().tearDown()

    def test_assign_delete_schedules_product_delete(self) -> None:
        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            ebay_receivers.ebay__assign__delete(
                sender=SalesChannelViewAssign,
                instance=self.assign,
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
        self.assertEqual(task.task_name, get_import_path(ebay_receivers.delete_ebay_product_db_task))
        self.assertEqual(task.task_kwargs.get("product_id"), self.product.id)
        self.assertEqual(task.task_kwargs.get("view_id"), self.view.id)

    def test_product_delete_schedules_once_per_view_and_skips_assign_followups(self) -> None:
        other_view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="DE",
            remote_id="EBAY_DE",
        )
        other_assign = SalesChannelViewAssign.objects.create(
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=other_view,
            remote_product=self.remote_product,
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            ebay_receivers.ebay__product__delete(sender=self.product.__class__, instance=self.product)

        tasks = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).order_by("id")
        self.assertEqual(tasks.count(), initial_count + 2)
        scheduled_views = {task.task_kwargs.get("view_id") for task in tasks}
        self.assertSetEqual(scheduled_views, {self.view.id, other_view.id})
        self.assertEqual(ebay_receivers._PENDING_PRODUCT_DELETE_COUNTS.get(self.product.id), 2)

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            ebay_receivers.ebay__assign__delete(sender=SalesChannelViewAssign, instance=self.assign)
        self.assertEqual(
            IntegrationTaskQueue.objects.filter(
                integration_id=self.sales_channel.id,
            ).count(),
            initial_count + 2,
        )
        self.assertEqual(ebay_receivers._PENDING_PRODUCT_DELETE_COUNTS.get(self.product.id), 1)

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            ebay_receivers.ebay__assign__delete(sender=SalesChannelViewAssign, instance=other_assign)
        self.assertNotIn(self.product.id, ebay_receivers._PENDING_PRODUCT_DELETE_COUNTS)
        self.assertEqual(
            IntegrationTaskQueue.objects.filter(
                integration_id=self.sales_channel.id,
            ).count(),
            initial_count + 2,
        )
