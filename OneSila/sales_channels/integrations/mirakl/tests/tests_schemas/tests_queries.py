from django.test import TransactionTestCase
from model_bakery import baker

from currencies.models import Currency
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from properties.models import Property, PropertySelectValue, ProductPropertiesRule
from sales_channels.integrations.mirakl.models import (
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklProductType,
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

MIRAKL_PROPERTY_FILTER_BY_SEARCH = """
query ($search: String!) {
  miraklProperties(filters: {search: $search}) {
    edges {
      node {
        id
        code
      }
    }
  }
}
"""

MIRAKL_PROPERTY_SELECT_VALUE_FILTER_BY_SEARCH = """
query ($search: String!) {
  miraklPropertySelectValues(filters: {search: $search}) {
    edges {
      node {
        id
        code
      }
    }
  }
}
"""

MIRAKL_PROPERTY_FILTER_BY_MAPPED_LOCALLY = """
query ($mappedLocally: Boolean!) {
  miraklProperties(filters: {mappedLocally: $mappedLocally}) {
    edges {
      node {
        id
        code
      }
    }
  }
}
"""

MIRAKL_PRODUCT_TYPE_FILTER_BY_MAPPED_LOCALLY = """
query ($mappedLocally: Boolean!) {
  miraklProductTypes(filters: {mappedLocally: $mappedLocally}) {
    edges {
      node {
        id
        remoteId
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
        self.product_rule = baker.make(
            ProductPropertiesRule,
            multi_tenant_company=self.multi_tenant_company,
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
        )

        response = self.strawberry_test_client(query=MIRAKL_MAPPING_QUERY)

        self.assertIsNone(response.errors)
        view_node = response.data["miraklSalesChannelViews"]["edges"][0]["node"]
        self.assertTrue(view_node["active"])

        currency_node = response.data["miraklRemoteCurrencies"]["edges"][0]["node"]
        self.assertEqual(currency_node["localInstance"]["name"], self.currency.name)
        self.assertEqual(currency_node["localInstance"]["symbol"], self.currency.symbol)
        self.assertEqual(currency_node["localInstance"]["isoCode"], self.currency.iso_code)

        select_value_node = response.data["miraklPropertySelectValues"]["edges"][0]["node"]
        self.assertEqual(select_value_node["label"], "Cotton")
        self.assertTrue(select_value_node["mappedLocally"])
        self.assertTrue(select_value_node["mappedRemotely"])
        self.assertEqual(select_value_node["remoteProperty"]["name"], remote_property.name)
        self.assertEqual(select_value_node["localInstance"]["value"], self.local_value.value)

    def test_mirakl_properties_can_filter_by_search(self):
        matching_property = baker.make(
            MiraklProperty,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            code="material",
            remote_id="material",
            name="Material",
        )
        baker.make(
            MiraklProperty,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            code="color",
            remote_id="color",
            name="Color",
        )

        response = self.strawberry_test_client(
            query=MIRAKL_PROPERTY_FILTER_BY_SEARCH,
            variables={"search": "mater"},
        )

        self.assertIsNone(response.errors)
        edges = response.data["miraklProperties"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(matching_property))

    def test_mirakl_property_select_values_can_filter_by_search(self):
        remote_property = baker.make(
            MiraklProperty,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            code="material",
            remote_id="material",
            name="Material",
        )
        matching_select_value = baker.make(
            MiraklPropertySelectValue,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_property=remote_property,
            code="cotton",
            remote_id="cotton",
            value="Cotton",
        )
        baker.make(
            MiraklPropertySelectValue,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_property=remote_property,
            code="linen",
            remote_id="linen",
            value="Linen",
        )

        response = self.strawberry_test_client(
            query=MIRAKL_PROPERTY_SELECT_VALUE_FILTER_BY_SEARCH,
            variables={"search": "cott"},
        )

        self.assertIsNone(response.errors)
        edges = response.data["miraklPropertySelectValues"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(matching_select_value))

    def test_mirakl_properties_can_filter_by_mapped_locally(self):
        mapped_property = baker.make(
            MiraklProperty,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=self.local_property,
            code="material",
            remote_id="material",
            name="Material",
        )
        baker.make(
            MiraklProperty,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            code="color",
            remote_id="color",
            name="Color",
        )

        response = self.strawberry_test_client(
            query=MIRAKL_PROPERTY_FILTER_BY_MAPPED_LOCALLY,
            variables={"mappedLocally": True},
        )

        self.assertIsNone(response.errors)
        edges = response.data["miraklProperties"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(mapped_property))

    def test_mirakl_product_types_can_filter_by_mapped_locally(self):
        mapped_product_type = baker.make(
            MiraklProductType,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=self.product_rule,
            remote_id="mirakl_type_a",
            name="Type A",
        )
        baker.make(
            MiraklProductType,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="mirakl_type_b",
            name="Type B",
        )

        response = self.strawberry_test_client(
            query=MIRAKL_PRODUCT_TYPE_FILTER_BY_MAPPED_LOCALLY,
            variables={"mappedLocally": True},
        )

        self.assertIsNone(response.errors)
        edges = response.data["miraklProductTypes"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(mapped_product_type))
