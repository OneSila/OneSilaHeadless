from unittest.mock import patch

from django.test import TransactionTestCase
from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from products.models import Product
from sales_channels.integrations.shein.models import (
    SheinProduct,
    SheinSalesChannel,
    SheinSalesChannelView,
)
from sales_channels.integrations.shein.tasks import (
    create_shein_product_db_task,
    update_shein_product_db_task,
)
from sales_channels.models import SalesChannelViewAssign


UPDATE_SHEIN_PRODUCT_MUTATION = """
mutation ($product: ProductPartialInput!, $salesChannel: SheinSalesChannelPartialInput!, $forceUpdate: Boolean!) {
  updateSheinProduct(product: $product, salesChannel: $salesChannel, forceUpdate: $forceUpdate)
}
"""

BULK_UPDATE_SHEIN_PRODUCT_MUTATION = """
mutation ($assigns: [SalesChannelViewAssignPartialInput!]!, $forceUpdate: Boolean!) {
  bulkUpdateSheinProductFromAssigns(assigns: $assigns, forceUpdate: $forceUpdate)
}
"""


class SheinProductMutationTest(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.sales_channel_view = baker.make(
            SheinSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            is_default=True,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            active=True,
            sku="SKU-1",
        )
        self.remote_product = baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_id="SPU-1",
            remote_sku="SKU-1",
            spu_name="SKU-1",
        )
        self.assign = SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=self.sales_channel_view,
            remote_product=self.remote_product,
            status=SalesChannelViewAssign.STATUS_CREATED,
        )
        self.assign.status = SalesChannelViewAssign.STATUS_CREATED
        self.assign.save(update_fields=["status"])
        self.assign.refresh_from_db()

    @patch("sales_channels.integrations.shein.flows.tasks_runner.run_single_shein_product_task_flow")
    def test_update_shein_product_force_update_runs_create_task(self, run_flow):
        resp = self.strawberry_test_client(
            query=UPDATE_SHEIN_PRODUCT_MUTATION,
            variables={
                "product": {"id": self.to_global_id(self.product)},
                "salesChannel": {"id": self.to_global_id(self.sales_channel)},
                "forceUpdate": True,
            },
        )

        self.assertTrue(resp.errors is None)
        run_flow.assert_called_once()
        _, kwargs = run_flow.call_args
        self.assertEqual(kwargs["task_func"], create_shein_product_db_task)
        self.assertEqual(kwargs["sales_channel"], self.sales_channel)
        self.assertEqual(kwargs["product_id"], self.product.id)
        self.assertEqual(kwargs["number_of_remote_requests"], 1)

    @patch("sales_channels.integrations.shein.flows.tasks_runner.run_single_shein_product_task_flow")
    def test_bulk_update_shein_product_force_update_runs_create_task(self, run_flow):
        resp = self.strawberry_test_client(
            query=BULK_UPDATE_SHEIN_PRODUCT_MUTATION,
            variables={
                "assigns": [{"id": self.to_global_id(self.assign)}],
                "forceUpdate": True,
            },
        )

        self.assertTrue(resp.errors is None)
        run_flow.assert_called_once()
        _, kwargs = run_flow.call_args
        self.assertEqual(kwargs["task_func"], create_shein_product_db_task)
        self.assertEqual(kwargs["sales_channel"], self.sales_channel)
        self.assertEqual(kwargs["product_id"], self.product.id)
        self.assertEqual(kwargs["number_of_remote_requests"], 1)

    @patch("sales_channels.integrations.shein.flows.tasks_runner.run_single_shein_product_task_flow")
    def test_bulk_update_shein_product_runs_update_task(self, run_flow):
        resp = self.strawberry_test_client(
            query=BULK_UPDATE_SHEIN_PRODUCT_MUTATION,
            variables={
                "assigns": [{"id": self.to_global_id(self.assign)}],
                "forceUpdate": False,
            },
        )

        self.assertTrue(resp.errors is None)
        run_flow.assert_called_once()
        _, kwargs = run_flow.call_args
        self.assertEqual(kwargs["task_func"], update_shein_product_db_task)
        self.assertEqual(kwargs["sales_channel"], self.sales_channel)
        self.assertEqual(kwargs["product_id"], self.product.id)
        self.assertEqual(kwargs["number_of_remote_requests"], 1)
