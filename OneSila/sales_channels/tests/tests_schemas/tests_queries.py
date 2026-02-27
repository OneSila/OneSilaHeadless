from django.test import TransactionTestCase

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from sales_channels.integrations.ebay.models import EbayDocumentType, EbaySalesChannel


REMOTE_DOCUMENT_TYPE_FILTER_BY_SEARCH = """
query ($search: String!) {
  remoteDocumentTypes(filters: {search: $search}) {
    edges {
      node {
        id
        remoteId
        name
      }
    }
  }
}
"""


class RemoteDocumentTypeQueryTest(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = EbaySalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://ebay-remote-doc-type-search.test",
        )
        self.matched = EbayDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CERTIFICATE_OF_CONFORMITY",
            name="Certificate of Conformity",
        )
        EbayDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="USER_GUIDE_OR_MANUAL",
            name="User Guide",
        )

    def test_filter_by_search_remote_id(self):
        resp = self.strawberry_test_client(
            query=REMOTE_DOCUMENT_TYPE_FILTER_BY_SEARCH,
            variables={"search": self.matched.remote_id},
        )
        self.assertTrue(resp.errors is None)
        edges = resp.data["remoteDocumentTypes"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(self.matched))
