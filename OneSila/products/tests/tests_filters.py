from django.test import TransactionTestCase
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from products.models import SimpleProduct
from properties.models import Property, PropertySelectValue, ProductProperty
from sales_channels.models import SalesChannelViewAssign
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonProductBrowseNode,
)
from .tests_schemas.queries import (
    PRODUCTS_ASSIGNED_TO_VIEW_QUERY,
    PRODUCTS_NOT_ASSIGNED_TO_VIEW_QUERY,
    PRODUCTS_WITH_VALUE_SELECT_IDS_QUERY,
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
        AmazonProductBrowseNode.objects.create(
            product=self.p1,
            sales_channel=self.sales_channel,
            view=self.view1,
            recommended_browse_node_id="1",
            multi_tenant_company=self.multi_tenant_company,
        )
        SalesChannelViewAssign.objects.create(
            product=self.p1,
            sales_channel_view=self.view1,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

        AmazonProductBrowseNode.objects.create(
            product=self.p3,
            sales_channel=self.sales_channel,
            view=self.view2,
            recommended_browse_node_id="1",
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


class ProductFilterValueSelectIdsTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        self.value1 = PropertySelectValue.objects.create(
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.value2 = PropertySelectValue.objects.create(
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.value3 = PropertySelectValue.objects.create(
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.p1 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.p2 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.p3 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        ProductProperty.objects.create(
            product=self.p1,
            property=self.property,
            value_select=self.value1,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=self.p2,
            property=self.property,
            value_select=self.value2,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=self.p3,
            property=self.property,
            value_select=self.value3,
            multi_tenant_company=self.multi_tenant_company,
        )

    def _query_ids(self, ids):
        resp = self.strawberry_test_client(
            query=PRODUCTS_WITH_VALUE_SELECT_IDS_QUERY,
            variables={"ids": ids},
        )
        self.assertIsNone(resp.errors)
        expected_ids = {self.p1.id, self.p2.id, self.p3.id}
        found_ids = {
            int(self.from_global_id(edge["node"]["id"])[1])
            for edge in resp.data["products"]["edges"]
        }
        return found_ids & expected_ids

    def test_value_select_ids_filters_multiple(self):
        ids = self._query_ids(
            [self.to_global_id(self.value1), self.to_global_id(self.value2)],
        )
        self.assertSetEqual(ids, {self.p1.id, self.p2.id})

    def test_value_select_ids_filters_subset(self):
        ids = self._query_ids(
            [self.to_global_id(self.value1), self.to_global_id(self.value3)],
        )
        self.assertSetEqual(ids, {self.p1.id, self.p3.id})
