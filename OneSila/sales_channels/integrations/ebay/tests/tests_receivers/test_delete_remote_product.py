from __future__ import annotations

from unittest.mock import patch

from model_bakery import baker

from products.models import Product
from sales_channels.integrations.ebay import receivers as ebay_receivers
from sales_channels.integrations.ebay.models import EbayProduct
from sales_channels.integrations.ebay.models.sales_channels import EbaySalesChannelView
from sales_channels.integrations.ebay.tests.tests_factories.mixins import TestCaseEbayMixin
from sales_channels.models import SalesChannelViewAssign


class EbayDeleteReceiversTests(TestCaseEbayMixin):
    def setUp(self) -> None:
        super().setUp()
        run_flow_patcher = patch(
            "sales_channels.integrations.ebay.receivers.run_single_ebay_product_task_flow",
            autospec=True,
        )
        self.run_flow_mock = run_flow_patcher.start()
        self.addCleanup(run_flow_patcher.stop)

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
        ebay_receivers.ebay__assign__delete(
            sender=SalesChannelViewAssign,
            instance=self.assign,
        )

        self.assertTrue(self.run_flow_mock.called)
        kwargs = self.run_flow_mock.call_args.kwargs
        self.assertEqual(kwargs.get("task_func"), ebay_receivers.delete_ebay_product_db_task)
        self.assertEqual(kwargs.get("product_id"), self.product.id)
        self.assertEqual(kwargs.get("view"), self.view)

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

        ebay_receivers.ebay__product__delete(sender=self.product.__class__, instance=self.product)

        self.assertEqual(self.run_flow_mock.call_count, 4)
        scheduled_views = {call.kwargs.get("view") for call in self.run_flow_mock.call_args_list}
        self.assertSetEqual(scheduled_views, {self.view, other_view})
        self.assertEqual(ebay_receivers._PENDING_PRODUCT_DELETE_COUNTS.get(self.product.id), 2)

        self.run_flow_mock.reset_mock()
        ebay_receivers.ebay__assign__delete(sender=SalesChannelViewAssign, instance=self.assign)
        self.assertEqual(self.run_flow_mock.call_count, 0)
        self.assertEqual(ebay_receivers._PENDING_PRODUCT_DELETE_COUNTS.get(self.product.id), 1)

        ebay_receivers.ebay__assign__delete(sender=SalesChannelViewAssign, instance=other_assign)
        self.assertNotIn(self.product.id, ebay_receivers._PENDING_PRODUCT_DELETE_COUNTS)
        self.assertEqual(self.run_flow_mock.call_count, 0)
