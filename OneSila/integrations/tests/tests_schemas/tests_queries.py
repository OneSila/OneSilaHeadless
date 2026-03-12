from django.test import TransactionTestCase
from model_bakery import baker
from strawberry.relay import to_base64

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from sales_channels.integrations.mirakl.models import MiraklSalesChannel, MiraklSalesChannelImport
from sales_channels.integrations.mirakl.schema.types.types import MiraklSalesChannelType


INTEGRATIONS_QUERY = """
query {
  integrations {
    edges {
      node {
        id
        type
        connected
        proxyId
      }
    }
  }
}
"""

SALES_CHANNELS_QUERY = """
query {
  salesChannels {
    edges {
      node {
        id
        type
        proxyId
        miraklImports {
          id
          type
          status
        }
      }
    }
  }
}
"""


class MiraklIntegrationQueryTests(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
            sub_type="tesco",
        )

    def test_integrations_query_exposes_mirakl_type_connection_state_and_proxy_id(self):
        response = self.strawberry_test_client(query=INTEGRATIONS_QUERY)

        self.assertIsNone(response.errors)
        node = response.data["integrations"]["edges"][0]["node"]
        self.assertEqual(node["type"], self.sales_channel.sub_type)
        self.assertTrue(node["connected"])
        self.assertEqual(node["proxyId"], to_base64(MiraklSalesChannelType, self.sales_channel.pk))

    def test_sales_channels_query_exposes_mirakl_proxy_id_and_imports(self):
        import_process = baker.make(
            MiraklSalesChannelImport,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            type=MiraklSalesChannelImport.TYPE_SCHEMA,
            status=MiraklSalesChannelImport.STATUS_NEW,
        )

        response = self.strawberry_test_client(query=SALES_CHANNELS_QUERY)

        self.assertIsNone(response.errors)
        node = response.data["salesChannels"]["edges"][0]["node"]
        self.assertEqual(node["type"], self.sales_channel.sub_type)
        self.assertEqual(node["proxyId"], to_base64(MiraklSalesChannelType, self.sales_channel.pk))
        self.assertEqual(len(node["miraklImports"]), 1)
        self.assertEqual(node["miraklImports"][0]["id"], self.to_global_id(import_process))
        self.assertEqual(node["miraklImports"][0]["type"], MiraklSalesChannelImport.TYPE_SCHEMA)
