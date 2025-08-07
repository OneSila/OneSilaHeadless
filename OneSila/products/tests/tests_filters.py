from django.test import TransactionTestCase
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from products.models import SimpleProduct
from sales_channels.models import SalesChannelViewAssign
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
)
from .tests_schemas.queries import (
    PRODUCTS_ASSIGNED_TO_VIEW_QUERY,
    PRODUCTS_NOT_ASSIGNED_TO_VIEW_QUERY,
)


class ProductFilterSalesChannelViewTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.view1 = AmazonSalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.view2 = AmazonSalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.p1 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.p2 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.p3 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        SalesChannelViewAssign.objects.create(
            product=self.p1,
            sales_channel_view=self.view1,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        SalesChannelViewAssign.objects.create(
            product=self.p3,
            sales_channel_view=self.view2,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

    def _query_ids(self, query, variables):
        resp = self.strawberry_test_client(query=query, variables=variables)
        self.assertIsNone(resp.errors)
        expected_ids = {self.p1.id, self.p2.id, self.p3.id}
        found_ids = {
            int(self.from_global_id(edge["node"]["id"])[1])
            for edge in resp.data["products"]["edges"]
        }
        return found_ids & expected_ids

    def test_assigned_to_sales_channel_view(self):
        ids = self._query_ids(
            PRODUCTS_ASSIGNED_TO_VIEW_QUERY,
            {"view": self.to_global_id(self.view1)},
        )
        self.assertSetEqual(ids, {self.p1.id})

    def test_not_assigned_to_sales_channel_view(self):
        ids = self._query_ids(
            PRODUCTS_NOT_ASSIGNED_TO_VIEW_QUERY,
            {"view": self.to_global_id(self.view1)},
        )
        self.assertSetEqual(ids, {self.p2.id, self.p3.id})
