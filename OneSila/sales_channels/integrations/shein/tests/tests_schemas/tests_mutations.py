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

    @patch("sales_channels.integrations.shein.factories.task_queue.SheinSingleChannelAddTask")
    def test_update_shein_product_force_update_runs_create_task(self, task_runner_cls):
        resp = self.strawberry_test_client(
            query=UPDATE_SHEIN_PRODUCT_MUTATION,
            variables={
                "product": {"id": self.to_global_id(self.product)},
                "salesChannel": {"id": self.to_global_id(self.sales_channel)},
                "forceUpdate": True,
            },
        )

        self.assertTrue(resp.errors is None)
        task_runner_cls.assert_called_once_with(
            task_func=create_shein_product_db_task,
            sales_channel=self.sales_channel,
            number_of_remote_requests=1,
        )
        task_runner_cls.return_value.set_extra_task_kwargs.assert_called_once_with(
            product_id=self.product.id,
        )
        task_runner_cls.return_value.run.assert_called_once()

    @patch("sales_channels.integrations.shein.factories.task_queue.SheinSingleChannelAddTask")
    def test_bulk_update_shein_product_force_update_runs_create_task(self, task_runner_cls):
        resp = self.strawberry_test_client(
            query=BULK_UPDATE_SHEIN_PRODUCT_MUTATION,
            variables={
                "assigns": [{"id": self.to_global_id(self.assign)}],
                "forceUpdate": True,
            },
        )

        self.assertTrue(resp.errors is None)
        task_runner_cls.assert_called_once_with(
            task_func=create_shein_product_db_task,
            sales_channel=self.sales_channel,
            number_of_remote_requests=1,
        )
        task_runner_cls.return_value.set_extra_task_kwargs.assert_called_once_with(
            product_id=self.product.id,
        )
        task_runner_cls.return_value.run.assert_called_once()

    @patch("sales_channels.integrations.shein.factories.task_queue.SheinSingleChannelAddTask")
    def test_bulk_update_shein_product_runs_update_task(self, task_runner_cls):
        resp = self.strawberry_test_client(
            query=BULK_UPDATE_SHEIN_PRODUCT_MUTATION,
            variables={
                "assigns": [{"id": self.to_global_id(self.assign)}],
                "forceUpdate": False,
            },
        )

        self.assertTrue(resp.errors is None)
        task_runner_cls.assert_called_once_with(
            task_func=update_shein_product_db_task,
            sales_channel=self.sales_channel,
            number_of_remote_requests=1,
        )
        task_runner_cls.return_value.set_extra_task_kwargs.assert_called_once_with(
            product_id=self.product.id,
        )
        task_runner_cls.return_value.run.assert_called_once()
