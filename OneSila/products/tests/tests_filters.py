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
from workflows.models import Workflow, WorkflowProductAssignment, WorkflowState
from .tests_schemas.queries import (
    PRODUCTS_ASSIGNED_TO_VIEW_QUERY,
    PRODUCTS_NOT_ASSIGNED_TO_VIEW_QUERY,
    PRODUCTS_WITH_WORKFLOW_STATE_ID_QUERY,
    PRODUCTS_WITH_VALUE_SELECT_IDS_QUERY,
    PRODUCTS_WITH_VALUE_SELECT_ID_QUERY,
    PRODUCTS_WITH_PROPERTY_ID_QUERY,
    PRODUCTS_WITH_NOT_PROPERTY_ID_QUERY,
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
            remote_id="1",
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
            remote_id="1",
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
        self.color_property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        self.size_property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        self.color_red = PropertySelectValue.objects.create(
            property=self.color_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.color_blue = PropertySelectValue.objects.create(
            property=self.color_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.size_small = PropertySelectValue.objects.create(
            property=self.size_property,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.p1 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.p2 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.p3 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        ProductProperty.objects.create(
            product=self.p1,
            property=self.color_property,
            value_select=self.color_red,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=self.p2,
            property=self.color_property,
            value_select=self.color_red,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=self.p3,
            property=self.size_property,
            value_select=self.size_small,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=self.p1,
            property=self.size_property,
            value_select=self.size_small,
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
            [self.to_global_id(self.color_red), self.to_global_id(self.size_small)],
        )
        self.assertSetEqual(ids, {self.p1.id})

    def test_value_select_ids_filters_no_match(self):
        ids = self._query_ids(
            [self.to_global_id(self.color_blue), self.to_global_id(self.size_small)],
        )
        self.assertSetEqual(ids, set())

    def test_value_select_id_filters_single(self):
        resp = self.strawberry_test_client(
            query=PRODUCTS_WITH_VALUE_SELECT_ID_QUERY,
            variables={"id": self.to_global_id(self.color_red)},
        )
        self.assertIsNone(resp.errors)
        expected_ids = {self.p1.id, self.p2.id, self.p3.id}
        found_ids = {
            int(self.from_global_id(edge["node"]["id"])[1])
            for edge in resp.data["products"]["edges"]
        } & expected_ids
        self.assertSetEqual(found_ids, {self.p1.id, self.p2.id})

    def test_property_id_filters_single(self):
        resp = self.strawberry_test_client(
            query=PRODUCTS_WITH_PROPERTY_ID_QUERY,
            variables={"id": self.to_global_id(self.size_property)},
        )
        self.assertIsNone(resp.errors)
        expected_ids = {self.p1.id, self.p2.id, self.p3.id}
        found_ids = {
            int(self.from_global_id(edge["node"]["id"])[1])
            for edge in resp.data["products"]["edges"]
        } & expected_ids
        self.assertSetEqual(found_ids, {self.p1.id, self.p3.id})

    def test_exclude_property_id_filters_single(self):
        resp = self.strawberry_test_client(
            query=PRODUCTS_WITH_NOT_PROPERTY_ID_QUERY,
            variables={"id": self.to_global_id(self.size_property)},
        )
        self.assertIsNone(resp.errors)
        expected_ids = {self.p1.id, self.p2.id, self.p3.id}
        found_ids = {
            int(self.from_global_id(edge["node"]["id"])[1])
            for edge in resp.data["products"]["edges"]
        } & expected_ids
        self.assertSetEqual(found_ids, {self.p2.id})


class ProductFilterWorkflowStateTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.workflow = Workflow.objects.create(
            name="Add Products",
            code="ADD_PRODUCTS",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.state_untouched = WorkflowState.objects.create(
            workflow=self.workflow,
            value="Untouched",
            code="UNTOUCHED",
            sort_order=10,
            is_default=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.state_enrich = WorkflowState.objects.create(
            workflow=self.workflow,
            value="To Enrich",
            code="TO_ENRICH",
            sort_order=20,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.p1 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.p2 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.p3 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        WorkflowProductAssignment.objects.create(
            workflow=self.workflow,
            product=self.p1,
            workflow_state=self.state_untouched,
            multi_tenant_company=self.multi_tenant_company,
        )
        WorkflowProductAssignment.objects.create(
            workflow=self.workflow,
            product=self.p2,
            workflow_state=self.state_enrich,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_workflow_state_id_filters_products(self):
        resp = self.strawberry_test_client(
            query=PRODUCTS_WITH_WORKFLOW_STATE_ID_QUERY,
            variables={"id": self.to_global_id(self.state_untouched)},
        )
        self.assertIsNone(resp.errors)
        expected_ids = {self.p1.id, self.p2.id, self.p3.id}
        found_ids = {
            int(self.from_global_id(edge["node"]["id"])[1])
            for edge in resp.data["products"]["edges"]
        } & expected_ids
        self.assertSetEqual(found_ids, {self.p1.id})
