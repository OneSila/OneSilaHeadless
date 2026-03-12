from django.test import TransactionTestCase
from model_bakery import baker

from currencies.models import Currency
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from properties.models import Property, PropertySelectValue
from sales_channels.integrations.mirakl.models import (
    MiraklInternalProperty,
    MiraklInternalPropertyOption,
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklRemoteCurrency,
    MiraklSalesChannel,
    MiraklSalesChannelView,
)


MIRAKL_CHANNELS_QUERY = """
query {
  miraklChannels {
    edges {
      node {
        id
        hostname
        shopId
        apiKey
        connected
      }
    }
  }
}
"""

MIRAKL_MAPPING_QUERY = """
query {
  miraklSalesChannelViews {
    edges {
      node {
        id
        active
      }
    }
  }
  miraklRemoteCurrencies {
    edges {
      node {
        id
        localInstance {
          name
          symbol
          isoCode
        }
      }
    }
  }
  miraklInternalProperties {
    edges {
      node {
        code
        mappedLocally
        mappedRemotely
        localInstance {
          name
        }
        options {
          value
          localInstance {
            value
          }
        }
      }
    }
  }
  miraklPropertySelectValues {
    edges {
      node {
        code
        label
        mappedLocally
        mappedRemotely
        remoteProperty {
          name
        }
        localInstance {
          value
        }
      }
    }
  }
}
"""


class MiraklQueryTests(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )
        self.local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            name="Material",
            internal_name="material",
            type=Property.TYPES.SELECT,
        )
        self.local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=self.local_property,
            value="Cotton",
        )
        self.currency = baker.make(
            Currency,
            multi_tenant_company=self.multi_tenant_company,
            name="Euro",
            symbol="EUR",
            iso_code="EUR",
        )

    def test_mirakl_sales_channel_query_exposes_api_key_and_connected(self):
        response = self.strawberry_test_client(query=MIRAKL_CHANNELS_QUERY)

        self.assertIsNone(response.errors)
        node = response.data["miraklChannels"]["edges"][0]["node"]
        self.assertEqual(node["shopId"], self.sales_channel.shop_id)
        self.assertEqual(node["apiKey"], self.sales_channel.api_key)
        self.assertTrue(node["connected"])

    def test_mirakl_mapping_queries_expose_concrete_nested_types_and_mapping_flags(self):
        baker.make(
            MiraklSalesChannelView,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="FR",
            name="France",
        )
        baker.make(
            MiraklRemoteCurrency,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_code="EUR",
            local_instance=self.currency,
        )
        internal_property = baker.make(
            MiraklInternalProperty,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=self.local_property,
            code="condition",
            remote_id="condition",
            name="Condition",
            label="Condition",
        )
        baker.make(
            MiraklInternalPropertyOption,
            internal_property=internal_property,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=self.local_value,
            value="new",
            label="New",
        )
        remote_property = baker.make(
            MiraklProperty,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=self.local_property,
            code="material",
            remote_id="material",
            name="Material",
        )
        baker.make(
            MiraklPropertySelectValue,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_property=remote_property,
            local_instance=self.local_value,
            code="cotton",
            remote_id="cotton",
            value="Cotton",
            translated_value="Cotton Label",
        )

        response = self.strawberry_test_client(query=MIRAKL_MAPPING_QUERY)

        self.assertIsNone(response.errors)
        view_node = response.data["miraklSalesChannelViews"]["edges"][0]["node"]
        self.assertTrue(view_node["active"])

        currency_node = response.data["miraklRemoteCurrencies"]["edges"][0]["node"]
        self.assertEqual(currency_node["localInstance"]["name"], self.currency.name)
        self.assertEqual(currency_node["localInstance"]["symbol"], self.currency.symbol)
        self.assertEqual(currency_node["localInstance"]["isoCode"], self.currency.iso_code)

        internal_node = response.data["miraklInternalProperties"]["edges"][0]["node"]
        self.assertTrue(internal_node["mappedLocally"])
        self.assertTrue(internal_node["mappedRemotely"])
        self.assertEqual(internal_node["localInstance"]["name"], self.local_property.name)
        self.assertEqual(internal_node["options"][0]["value"], "new")
        self.assertEqual(internal_node["options"][0]["localInstance"]["value"], self.local_value.value)

        select_value_node = response.data["miraklPropertySelectValues"]["edges"][0]["node"]
        self.assertEqual(select_value_node["label"], "Cotton Label")
        self.assertTrue(select_value_node["mappedLocally"])
        self.assertTrue(select_value_node["mappedRemotely"])
        self.assertEqual(select_value_node["remoteProperty"]["name"], remote_property.name)
        self.assertEqual(select_value_node["localInstance"]["value"], self.local_value.value)
