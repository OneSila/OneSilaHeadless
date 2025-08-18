from django.test import TransactionTestCase
from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProduct,
    AmazonProductIssue,
    AmazonSalesChannelView,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonProductProperty,
)
from products.models import Product
from properties.models import Property, ProductProperty

from .queries import (
    AMAZON_PRODUCT_FILTER_BY_LOCAL_INSTANCE,
    AMAZON_PRODUCT_WITH_ISSUES,
    AMAZON_PRODUCT_PROPERTY_FILTER_BY_LOCAL_INSTANCE,
    AMAZON_PRODUCT_PROPERTY_FILTER_BY_REMOTE_SELECT_VALUE,
    AMAZON_PRODUCT_PROPERTY_FILTER_BY_REMOTE_PRODUCT,
)


class AmazonProductQueryTest(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
        )
        self.amazon_product = baker.make(
            AmazonProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )

    def test_filter_by_local_instance(self):
        resp = self.strawberry_test_client(
            query=AMAZON_PRODUCT_FILTER_BY_LOCAL_INSTANCE,
            variables={"localInstance": self.to_global_id(self.product)},
        )
        self.assertTrue(resp.errors is None)
        edges = resp.data["amazonProducts"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(self.amazon_product))


class AmazonProductPropertyQueryTest(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
        )
        self.amazon_product = baker.make(
            AmazonProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        self.property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product_property = baker.make(
            ProductProperty,
            product=self.product,
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.amazon_property = baker.make(
            AmazonProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.property,
        )
        self.marketplace = baker.make(
            AmazonSalesChannelView,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_select_value = baker.make(
            AmazonPropertySelectValue,
            amazon_property=self.amazon_property,
            marketplace=self.marketplace,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_value="VAL",
        )
        self.amazon_product_property = baker.make(
            AmazonProductProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product_property,
            remote_product=self.amazon_product,
            remote_property=self.amazon_property,
            remote_select_value=self.remote_select_value,
        )

    def test_filter_by_local_instance(self):
        resp = self.strawberry_test_client(
            query=AMAZON_PRODUCT_PROPERTY_FILTER_BY_LOCAL_INSTANCE,
            variables={"localInstance": self.to_global_id(self.product_property)},
        )
        self.assertTrue(resp.errors is None)
        edges = resp.data["amazonProductProperties"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(self.amazon_product_property))

    def test_filter_by_remote_select_value(self):
        resp = self.strawberry_test_client(
            query=AMAZON_PRODUCT_PROPERTY_FILTER_BY_REMOTE_SELECT_VALUE,
            variables={"remoteSelectValue": self.to_global_id(self.remote_select_value)},
        )
        self.assertTrue(resp.errors is None)
        edges = resp.data["amazonProductProperties"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(self.amazon_product_property))

    def test_filter_by_remote_product(self):
        resp = self.strawberry_test_client(
            query=AMAZON_PRODUCT_PROPERTY_FILTER_BY_REMOTE_PRODUCT,
            variables={"remoteProduct": self.to_global_id(self.amazon_product)},
        )
        self.assertTrue(resp.errors is None)
        edges = resp.data["amazonProductProperties"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(self.amazon_product_property))


class AmazonProductIssuesQueryTest(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
        )
        self.amazon_product = baker.make(
            AmazonProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        self.view = baker.make(
            AmazonSalesChannelView,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.issue = baker.make(
            AmazonProductIssue,
            remote_product=self.amazon_product,
            view=self.view,
            multi_tenant_company=self.multi_tenant_company,
            code="ISSUE_CODE",
            message="Problem",
        )

    def test_product_issues(self):
        resp = self.strawberry_test_client(
            query=AMAZON_PRODUCT_WITH_ISSUES,
            variables={"id": self.to_global_id(self.amazon_product)},
        )
        self.assertTrue(resp.errors is None)
        issues = resp.data["amazonProduct"]["issues"]
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["code"], self.issue.code)
