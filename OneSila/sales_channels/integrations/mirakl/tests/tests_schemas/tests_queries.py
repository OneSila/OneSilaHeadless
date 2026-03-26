from django.core.files.base import ContentFile
from django.utils import timezone
from django.test import TransactionTestCase
from model_bakery import baker
from strawberry.relay import to_base64

from currencies.models import Currency
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from products.models import Product, ProductTranslation
from properties.models import (
    Property,
    PropertySelectValue,
    PropertySelectValueTranslation,
    PropertyTranslation,
    ProductPropertiesRule,
)
from sales_channels.integrations.mirakl.models import (
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklProductType,
    MiraklProductIssue,
    MiraklRemoteCurrency,
    MiraklProduct,
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
    MiraklSalesChannelFeedItem,
    MiraklSalesChannelImport,
    MiraklSalesChannelImportExportFile,
    MiraklSalesChannelView,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


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
        lastDifferentialIssuesFetch
        lastFullIssuesFetch
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

MIRAKL_PRODUCT_ISSUES_FILTER_QUERY = """
query ($view: GlobalID, $isRejected: Boolean!) {
  miraklProductIssues(filters: {views: {id: {exact: $view}}, isRejected: {exact: $isRejected}}) {
    edges {
      node {
        id
        mainCode
        code
        severity
        isRejected
        views {
          remoteId
        }
      }
    }
  }
}
"""

MIRAKL_PRODUCT_ISSUES_FILTER_BY_REMOTE_PRODUCT_LOCAL_INSTANCE_QUERY = """
query ($localInstance: GlobalID!) {
  miraklProductIssues(filters: {remoteProduct: {localInstance: {id: {exact: $localInstance}}}}) {
    edges {
      node {
        id
      }
    }
  }
}
"""

MIRAKL_PRODUCT_ISSUE_NODE_QUERY = """
query ($id: GlobalID!) {
  miraklProductIssue(id: $id) {
    id
    mainCode
    code
    views {
      remoteId
    }
    remoteProduct {
      id
    }
  }
}
"""

MIRAKL_FEEDS_QUERY = """
query ($status: String!, $importStatus: String!) {
  miraklFeeds(filters: {status: {exact: $status}, importStatus: {exact: $importStatus}}) {
    edges {
      node {
        id
        status
        importStatus
        conversionType
        conversionOptionsAiEnrichmentEnabled
        conversionOptionsAiRewriteEnabled
        integrationDetailsInvalidProducts
        itemsCount
        rowsCount
        fileUrl
        errorReportFileUrl
        newProductReportFileUrl
        transformedFileUrl
        transformationErrorReportFileUrl
        products {
          id
          sku
          name
        }
      }
    }
  }
}
"""

MIRAKL_IMPORT_EXPORT_FILES_QUERY = """
query {
  miraklImportExportFiles {
    edges {
      node {
        id
        fileUrl
        importProcess {
          id
          type
        }
      }
    }
  }
}
"""


class MiraklQueryTests(
    DisableMiraklConnectionMixin,
    TransactionTestCaseMixin,
    TransactionTestCase,
):
    def _create_local_property(self, *, name: str, internal_name: str, property_type: str) -> Property:
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            internal_name=internal_name,
            type=property_type,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=local_property,
            language=self.multi_tenant_company.language,
            name=name,
        )
        return local_property

    def _create_local_select_value(self, *, property_instance: Property, value: str) -> PropertySelectValue:
        local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=property_instance,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=local_value,
            language=self.multi_tenant_company.language,
            value=value,
        )
        return local_value

    def _create_local_product(self, *, sku: str, name: str) -> Product:
        product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            sku=sku,
            type=Product.SIMPLE,
        )
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            language=self.multi_tenant_company.language,
            name=name,
        )
        return product

    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )
        self.local_property = self._create_local_property(
            name="Material",
            internal_name="material",
            property_type=Property.TYPES.SELECT,
        )
        self.local_value = self._create_local_select_value(
            property_instance=self.local_property,
            value="Cotton",
        )
        self.currency = baker.make(
            Currency,
            multi_tenant_company=self.multi_tenant_company,
            name="Euro",
            symbol="EUR",
            iso_code="EUR",
        )
        product_type_property = Property.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True,
        )
        product_type_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=product_type_property,
        )
        self.product_rule = ProductPropertiesRule.objects.get(
            product_type=product_type_value,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel__isnull=True,
        )

    def test_mirakl_sales_channel_query_exposes_api_key_and_connected(self):
        self.sales_channel.last_differential_issues_fetch = timezone.now()
        self.sales_channel.last_full_issues_fetch = timezone.now()
        self.sales_channel.save(update_fields=["last_differential_issues_fetch", "last_full_issues_fetch"])
        response = self.strawberry_test_client(query=MIRAKL_CHANNELS_QUERY)

        self.assertIsNone(response.errors)
        node = response.data["miraklChannels"]["edges"][0]["node"]
        self.assertEqual(node["shopId"], self.sales_channel.shop_id)
        self.assertEqual(node["apiKey"], self.sales_channel.api_key)
        self.assertTrue(node["connected"])
        self.assertIsNotNone(node["lastDifferentialIssuesFetch"])
        self.assertIsNotNone(node["lastFullIssuesFetch"])

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
        baker.make(
            MiraklProperty,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            code="logistic_class",
            remote_id="logistic_class",
            name="Logistic class",
            representation_type=MiraklProperty.REPRESENTATION_LOGISTIC_CLASS,
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

    def test_mirakl_product_issues_can_filter_by_view_and_is_rejected(self):
        remote_product = baker.make(
            MiraklProduct,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_sku="shopSku1",
        )
        view = baker.make(
            MiraklSalesChannelView,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="FR",
            name="France",
        )
        matching_issue = baker.make(
            MiraklProductIssue,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=remote_product,
            main_code="MCM-04012",
            code="2",
            severity="ERROR",
            is_rejected=True,
        )
        matching_issue.views.add(view)
        other_issue = baker.make(
            MiraklProductIssue,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=remote_product,
            main_code="MCM-05000",
            code="MCM-05000",
            severity="WARNING",
            is_rejected=False,
        )

        response = self.strawberry_test_client(
            query=MIRAKL_PRODUCT_ISSUES_FILTER_QUERY,
            variables={"view": self.to_global_id(view), "isRejected": True},
        )

        self.assertIsNone(response.errors)
        edges = response.data["miraklProductIssues"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(matching_issue))
        self.assertEqual(edges[0]["node"]["views"][0]["remoteId"], "FR")
        self.assertNotEqual(edges[0]["node"]["id"], self.to_global_id(other_issue))

    def test_mirakl_product_issue_node_query_returns_views_and_remote_product(self):
        remote_product = baker.make(
            MiraklProduct,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_sku="shopSku1",
        )
        view = baker.make(
            MiraklSalesChannelView,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="BE",
            name="Belgium",
        )
        issue = baker.make(
            MiraklProductIssue,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=remote_product,
            main_code="MCM-04012",
            code="2",
            severity="ERROR",
            is_rejected=True,
        )
        issue.views.add(view)

        response = self.strawberry_test_client(
            query=MIRAKL_PRODUCT_ISSUE_NODE_QUERY,
            variables={"id": self.to_global_id(issue)},
        )

        self.assertIsNone(response.errors)
        node = response.data["miraklProductIssue"]
        self.assertEqual(node["id"], self.to_global_id(issue))
        self.assertEqual(
            node["remoteProduct"]["id"],
            to_base64("MiraklRemoteProductType", remote_product.id),
        )
        self.assertEqual(node["views"][0]["remoteId"], "BE")

    def test_mirakl_product_issues_can_filter_by_remote_product_local_instance(self):
        matching_product = self._create_local_product(
            sku="LOCAL-SKU-REMOTE-1",
            name="Local Product Remote 1",
        )
        other_product = self._create_local_product(
            sku="LOCAL-SKU-REMOTE-2",
            name="Local Product Remote 2",
        )
        matching_remote_product = baker.make(
            MiraklProduct,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=matching_product,
            remote_sku="shopSkuRemote1",
        )
        other_remote_product = baker.make(
            MiraklProduct,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=other_product,
            remote_sku="shopSkuRemote2",
        )
        matching_issue = baker.make(
            MiraklProductIssue,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=matching_remote_product,
            main_code="MCM-04012",
            code="2",
            severity="ERROR",
            is_rejected=True,
        )
        baker.make(
            MiraklProductIssue,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=other_remote_product,
            main_code="MCM-05000",
            code="MCM-05000",
            severity="WARNING",
            is_rejected=False,
        )

        response = self.strawberry_test_client(
            query=MIRAKL_PRODUCT_ISSUES_FILTER_BY_REMOTE_PRODUCT_LOCAL_INSTANCE_QUERY,
            variables={"localInstance": self.to_global_id(matching_product)},
        )

        self.assertIsNone(response.errors)
        edges = response.data["miraklProductIssues"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(matching_issue))

    def test_mirakl_feeds_query_exposes_mirakl_specific_fields(self):
        product_type = baker.make(
            MiraklProductType,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        feed = baker.make(
            MiraklSalesChannelFeed,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            type=MiraklSalesChannelFeed.TYPE_COMBINED,
            status=MiraklSalesChannelFeed.STATUS_SUBMITTED,
            import_status="COMPLETE",
            conversion_type="AI_CONVERTER",
            conversion_options_ai_enrichment_enabled=True,
            conversion_options_ai_rewrite_enabled=False,
            integration_details_invalid_products=3,
            items_count=2,
            rows_count=5,
            product_type=product_type,
        )
        feed.file.save("feed.csv", ContentFile("feed"), save=True)
        feed.error_report_file.save("errors.csv", ContentFile("err"), save=True)
        feed.new_product_report_file.save("new.csv", ContentFile("new"), save=True)
        feed.transformed_file.save("transformed.csv", ContentFile("transformed"), save=True)
        feed.transformation_error_report_file.save("transform-errors.csv", ContentFile("transform"), save=True)

        baker.make(
            MiraklSalesChannelFeedItem,
            feed=feed,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=baker.make(
                MiraklProduct,
                sales_channel=self.sales_channel,
                multi_tenant_company=self.multi_tenant_company,
                local_instance=self._create_local_product(
                    sku="LOCAL-SKU-1",
                    name="Local Product 1",
                ),
            ),
        )

        response = self.strawberry_test_client(
            query=MIRAKL_FEEDS_QUERY,
            variables={
                "status": MiraklSalesChannelFeed.STATUS_SUBMITTED,
                "importStatus": "COMPLETE",
            },
        )

        self.assertIsNone(response.errors)
        node = response.data["miraklFeeds"]["edges"][0]["node"]
        self.assertEqual(node["conversionType"], "AI_CONVERTER")
        self.assertTrue(node["conversionOptionsAiEnrichmentEnabled"])
        self.assertFalse(node["conversionOptionsAiRewriteEnabled"])
        self.assertEqual(node["integrationDetailsInvalidProducts"], 3)
        self.assertEqual(node["itemsCount"], 2)
        self.assertEqual(node["rowsCount"], 5)
        self.assertIsNotNone(node["fileUrl"])
        self.assertIsNotNone(node["errorReportFileUrl"])
        self.assertIsNotNone(node["newProductReportFileUrl"])
        self.assertIsNotNone(node["transformedFileUrl"])
        self.assertIsNotNone(node["transformationErrorReportFileUrl"])
        self.assertEqual(len(node["products"]), 1)
        self.assertEqual(node["products"][0]["sku"], "LOCAL-SKU-1")

    def test_mirakl_import_export_files_query_exposes_file_url_and_import_process(self):
        import_process = baker.make(
            MiraklSalesChannelImport,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            type=MiraklSalesChannelImport.TYPE_PRODUCTS,
        )
        export_file = baker.make(
            MiraklSalesChannelImportExportFile,
            import_process=import_process,
            multi_tenant_company=self.multi_tenant_company,
        )
        export_file.file.save("mirakl-export.xlsx", ContentFile(b"xlsx"), save=True)

        response = self.strawberry_test_client(query=MIRAKL_IMPORT_EXPORT_FILES_QUERY)

        self.assertIsNone(response.errors)
        node = response.data["miraklImportExportFiles"]["edges"][0]["node"]
        self.assertEqual(node["importProcess"]["id"], self.to_global_id(import_process))
        self.assertEqual(node["importProcess"]["type"], MiraklSalesChannelImport.TYPE_PRODUCTS)
        self.assertIsNotNone(node["fileUrl"])
