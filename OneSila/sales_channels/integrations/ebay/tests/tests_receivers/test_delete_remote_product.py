from __future__ import annotations

from unittest.mock import patch

from model_bakery import baker

from sales_channels.integrations.ebay import receivers as ebay_receivers
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
        self.product = baker.make(
            "products.Product",
            sku="SKU-1",
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

    @patch("sales_channels.integrations.ebay.receivers.run_single_ebay_product_task_flow")
    def test_assign_delete_schedules_product_delete(self, mock_run_flow) -> None:
        ebay_receivers.ebay__assign__delete(
            sender=SalesChannelViewAssign,
            instance=self.assign,
        )

        self.assertTrue(mock_run_flow.called)
        kwargs = mock_run_flow.call_args.kwargs
        self.assertEqual(kwargs.get("task_func"), ebay_receivers.delete_ebay_product_db_task)
        self.assertEqual(kwargs.get("product_id"), self.product.id)
        self.assertEqual(kwargs.get("view"), self.view)

    @patch("sales_channels.integrations.ebay.receivers.run_single_ebay_product_task_flow")
    def test_product_delete_schedules_once_per_view_and_skips_assign_followups(self, mock_run_flow) -> None:
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

        ebay_receivers.ebay__product__delete(sender=self.product.__class__, instance=self.product)

        self.assertEqual(mock_run_flow.call_count, 2)
        scheduled_views = {call.kwargs.get("view") for call in mock_run_flow.call_args_list}
        self.assertSetEqual(scheduled_views, {self.view, other_view})
        self.assertEqual(ebay_receivers._PENDING_PRODUCT_DELETE_COUNTS.get(self.product.id), 2)

        mock_run_flow.reset_mock()
        ebay_receivers.ebay__assign__delete(sender=SalesChannelViewAssign, instance=self.assign)
        self.assertEqual(mock_run_flow.call_count, 0)
        self.assertEqual(ebay_receivers._PENDING_PRODUCT_DELETE_COUNTS.get(self.product.id), 1)

        ebay_receivers.ebay__assign__delete(sender=SalesChannelViewAssign, instance=other_assign)
        self.assertNotIn(self.product.id, ebay_receivers._PENDING_PRODUCT_DELETE_COUNTS)
        self.assertEqual(mock_run_flow.call_count, 0)
