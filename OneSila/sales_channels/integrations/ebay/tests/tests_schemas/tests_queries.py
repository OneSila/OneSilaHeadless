from django.test import TransactionTestCase

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from properties.models import Property
from sales_channels.integrations.ebay.models import EbayCategory, EbayInternalProperty, EbaySalesChannel


EBAY_CATEGORY_FILTER_BY_SEARCH = """
query ($search: String!) {
  ebayCategories(filters: {search: $search}) {
    edges {
      node {
        id
        remoteId
      }
    }
  }
}
"""


class EbayCategoryQueryTest(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.category = EbayCategory.objects.create(
            marketplace_default_tree_id="TREE-1",
            remote_id="12345",
            name="Category 12345",
            full_name="Root > Category 12345",
        )
        EbayCategory.objects.create(
            marketplace_default_tree_id="TREE-1",
            remote_id="67890",
            name="Category 67890",
            full_name="Root > Category 67890",
        )

    def test_filter_by_search_remote_id(self):
        resp = self.strawberry_test_client(
            query=EBAY_CATEGORY_FILTER_BY_SEARCH,
            variables={"search": self.category.remote_id},
        )
        self.assertTrue(resp.errors is None)
        edges = resp.data["ebayCategories"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(self.category))


EBAY_INTERNAL_PROPERTY_ALLOWED_TYPES_QUERY = """
query ($id: ID!) {
  ebayInternalProperty(id: $id) {
    id
    code
    allowedTypes
  }
}
"""


class EbayInternalPropertyQueryTest(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = EbaySalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://ebay.query.test",
        )
        self.internal_property = EbayInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="isbn",
            name="ISBN",
            type=Property.TYPES.TEXT,
            is_root=False,
        )

    def test_allowed_types_is_exposed(self):
        resp = self.strawberry_test_client(
            query=EBAY_INTERNAL_PROPERTY_ALLOWED_TYPES_QUERY,
            variables={"id": self.to_global_id(self.internal_property)},
        )
        self.assertTrue(resp.errors is None)
        self.assertEqual(
            resp.data["ebayInternalProperty"]["allowedTypes"],
            ["TEXT", "DESCRIPTION", "INT"],
        )
