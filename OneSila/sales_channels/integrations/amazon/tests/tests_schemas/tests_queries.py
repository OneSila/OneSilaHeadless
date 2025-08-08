from django.test import TransactionTestCase
from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProduct,
    AmazonProductIssue,
    AmazonSalesChannelView,
)
from products.models import Product

from .queries import (
    AMAZON_PRODUCT_FILTER_BY_LOCAL_INSTANCE,
    AMAZON_PRODUCT_WITH_ISSUES,
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
