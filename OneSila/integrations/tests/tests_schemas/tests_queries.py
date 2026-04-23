from django.test import TransactionTestCase
from django.core.files.base import ContentFile
from model_bakery import baker
from strawberry.relay import to_base64

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from integrations.helpers import _get_public_integration_type_cached
from integrations.models import (
    PublicIntegrationType,
    PublicIntegrationTypeTranslation,
    PublicIssue,
    PublicIssueCategory,
    PublicIssueImage,
)
from integrations.tests.helpers import PublicIntegrationTypeSchemaMixin, PublicIssueSchemaMixin
from media.tests.helpers import CreateImageMixin
from sales_channels.integrations.mirakl.models import MiraklSalesChannel, MiraklSalesChannelImport
from sales_channels.integrations.mirakl.schema.types.types import MiraklSalesChannelType
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


INTEGRATIONS_QUERY = """
query {
  integrations {
    edges {
      node {
        id
        type
        connected
        proxyId
        iconSvgUrl
        logoPngUrl
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
        iconSvg
        logoPng
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

PUBLIC_INTEGRATION_TYPES_QUERY = """
query PublicIntegrationTypes($search: String!) {
  publicIntegrationTypes(filters: {search: $search}) {
    edges {
      node {
        key
        type
        subtype
        category
        active
        isBeta
        supportsOpenAiProductFeed
        sortOrder
        name(language: "de")
        description(language: "de")
        basedTo {
          key
        }
      }
    }
  }
}
"""

PUBLIC_ISSUES_QUERY = """
query PublicIssues($search: String!, $categoryCode: String!, $integrationType: String!) {
  publicIssues(filters: {
    search: $search,
    categoryCode: $categoryCode,
    integrationTypeType: $integrationType
  }) {
    edges {
      node {
        code
        issue
        cause
        recommendedFix
        integrationType {
          key
          type
        }
        categories {
          name
          code
        }
      }
    }
  }
}
"""

PUBLIC_ISSUE_CATEGORIES_QUERY = """
query PublicIssueCategories {
  publicIssueCategories {
    edges {
      node {
        name
        code
      }
    }
  }
}
"""

PUBLIC_ISSUE_QUERY = """
query PublicIssue($id: GlobalID!) {
  publicIssue(id: $id) {
    id
    code
    issue
    recommendedFix
    categories {
      code
    }
    images {
      imageUrl
    }
  }
}
"""


class MiraklIntegrationQueryTests(
    CreateImageMixin,
    PublicIntegrationTypeSchemaMixin,
    DisableMiraklConnectionMixin,
    TransactionTestCaseMixin,
    TransactionTestCase,
):
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
        self.mirakl_base_public_type, _ = PublicIntegrationType.objects.update_or_create(
            key="mirakl",
            defaults={
                "type": "mirakl",
                "category": PublicIntegrationType.CATEGORY_MARKETPLACE,
                "active": True,
                "sort_order": 1,
            },
        )
        PublicIntegrationTypeTranslation.objects.update_or_create(
            public_integration_type=self.mirakl_base_public_type,
            language="en",
            defaults={
                "name": "Mirakl",
                "description": "Mirakl base integration",
            },
        )
        self.mirakl_subtype_public_type, _ = PublicIntegrationType.objects.update_or_create(
            key="tesco",
            defaults={
                "type": "mirakl",
                "subtype": "tesco",
                "based_to": self.mirakl_base_public_type,
                "category": PublicIntegrationType.CATEGORY_MARKETPLACE,
                "active": True,
                "sort_order": 2,
            },
        )
        PublicIntegrationTypeTranslation.objects.update_or_create(
            public_integration_type=self.mirakl_subtype_public_type,
            language="en",
            defaults={
                "name": "Tesco",
                "description": "Mirakl Tesco integration",
            },
        )
        _get_public_integration_type_cached.cache_clear()

        self.mirakl_base_public_type.logo_png.save("mirakl-base.png", self.get_image_file("red.png"), save=True)
        self.mirakl_base_public_type.logo_svg.save(
            "mirakl-base.svg",
            ContentFile(b"<svg xmlns='http://www.w3.org/2000/svg'></svg>"),
            save=True,
        )
        self.mirakl_subtype_public_type.logo_png.save("tesco-public.png", self.get_image_file("red.png"), save=True)
        self.mirakl_subtype_public_type.logo_svg.save(
            "tesco-public.svg",
            ContentFile(b"<svg xmlns='http://www.w3.org/2000/svg'></svg>"),
            save=True,
        )
        self.expected_subtype_logo_png_name = self.mirakl_subtype_public_type.logo_png.name.rsplit("/", 1)[-1]
        self.expected_subtype_logo_svg_name = self.mirakl_subtype_public_type.logo_svg.name.rsplit("/", 1)[-1]

    def test_integrations_query_exposes_mirakl_type_connection_state_and_proxy_id(self):
        response = self.strawberry_test_client(query=INTEGRATIONS_QUERY)

        self.assertIsNone(response.errors)
        node = response.data["integrations"]["edges"][0]["node"]
        self.assertEqual(node["type"], self.sales_channel.sub_type)
        self.assertTrue(node["connected"])
        self.assertEqual(node["proxyId"], to_base64(MiraklSalesChannelType, self.sales_channel.pk))
        self.assertTrue(node["iconSvgUrl"].startswith("http"))
        self.assertTrue(node["logoPngUrl"].startswith("http"))
        self.assertTrue(node["iconSvgUrl"].endswith(self.expected_subtype_logo_svg_name))
        self.assertTrue(node["logoPngUrl"].endswith(self.expected_subtype_logo_png_name))

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
        self.assertTrue(node["iconSvg"].startswith("http"))
        self.assertTrue(node["logoPng"].startswith("http"))
        self.assertTrue(node["iconSvg"].endswith(self.expected_subtype_logo_svg_name))
        self.assertTrue(node["logoPng"].endswith(self.expected_subtype_logo_png_name))
        self.assertEqual(len(node["miraklImports"]), 1)
        self.assertEqual(node["miraklImports"][0]["id"], self.to_global_id(import_process))
        self.assertEqual(node["miraklImports"][0]["type"], MiraklSalesChannelImport.TYPE_SCHEMA)


class PublicIntegrationTypeQueryTests(
    PublicIntegrationTypeSchemaMixin,
    TransactionTestCaseMixin,
    TransactionTestCase,
):
    def setUp(self):
        super().setUp()
        self.base_type = PublicIntegrationType.objects.create(
            key="shopify_query_test",
            type="channel",
            subtype="saas",
            category=PublicIntegrationType.CATEGORY_STOREFRONT,
            active=True,
            supports_open_ai_product_feed=True,
            sort_order=1,
        )
        PublicIntegrationTypeTranslation.objects.create(
            public_integration_type=self.base_type,
            language="en",
            name="Shopify Query",
            description="English storefront",
        )

        self.variant_type = PublicIntegrationType.objects.create(
            key="shopify_plus_query_test",
            type="channel",
            subtype="enterprise",
            based_to=self.base_type,
            category=PublicIntegrationType.CATEGORY_STOREFRONT,
            active=True,
            is_beta=True,
            sort_order=2,
        )
        PublicIntegrationTypeTranslation.objects.create(
            public_integration_type=self.variant_type,
            language="de",
            name="Shopify Plus Query",
            description="Deutsche Beschreibung",
        )
        PublicIntegrationTypeTranslation.objects.create(
            public_integration_type=self.variant_type,
            language="en",
            name="Shopify Plus Query EN",
            description="",
        )

    def test_public_integration_types_query_filters_and_resolves_translated_fields(self):
        response = self.strawberry_test_client(
            query=PUBLIC_INTEGRATION_TYPES_QUERY,
            variables={"search": "Plus"},
        )

        self.assertIsNone(response.errors)
        edges = response.data["publicIntegrationTypes"]["edges"]
        self.assertEqual(len(edges), 1)

        node = edges[0]["node"]
        self.assertEqual(node["key"], self.variant_type.key)
        self.assertEqual(node["name"], "Shopify Plus Query")
        self.assertEqual(node["description"], "Deutsche Beschreibung")
        self.assertEqual(node["basedTo"]["key"], self.base_type.key)
        self.assertTrue(node["isBeta"])
        self.assertFalse(node["supportsOpenAiProductFeed"])


class PublicIssueQueryTests(
    PublicIssueSchemaMixin,
    TransactionTestCaseMixin,
    TransactionTestCase,
):
    def setUp(self):
        super().setUp()
        self.ebay_type = PublicIntegrationType.objects.create(
            key="ebay_public_issue_query_test",
            type="ebay",
            category=PublicIntegrationType.CATEGORY_MARKETPLACE,
        )
        self.amazon_type = PublicIntegrationType.objects.create(
            key="amazon_public_issue_query_test",
            type="amazon",
            category=PublicIntegrationType.CATEGORY_MARKETPLACE,
        )
        self.matching_issue = PublicIssue.objects.create(
            integration_type=self.ebay_type,
            code="1234",
            issue="Ebay rejected the listing because a required aspect is missing.",
            cause="The color aspect is required for this category.",
            recommended_fix="Fill the color attribute and retry the listing sync.",
        )
        PublicIssueCategory.objects.create(
            public_issue=self.matching_issue,
            name="Product Data",
            code="PRODUCT_DATA",
        )
        PublicIssueImage.objects.create(
            public_issue=self.matching_issue,
            image=ContentFile(b"image", name="issue-image.jpg"),
        )
        other_issue = PublicIssue.objects.create(
            integration_type=self.amazon_type,
            code="5678",
            issue="Amazon rejected the feed because a browse node is missing.",
            cause="The product type requires a browse node.",
            recommended_fix="Map a valid browse node.",
        )
        PublicIssueCategory.objects.create(
            public_issue=other_issue,
            name="Catalog",
            code="CATALOG",
        )

    def test_public_issues_query_filters_by_search_category_and_integration_type(self):
        response = self.strawberry_test_client(
            query=PUBLIC_ISSUES_QUERY,
            variables={
                "search": "color",
                "categoryCode": "PRODUCT_DATA",
                "integrationType": "ebay",
            },
        )

        self.assertIsNone(response.errors)
        edges = response.data["publicIssues"]["edges"]
        self.assertEqual(len(edges), 1)
        node = edges[0]["node"]
        self.assertEqual(node["code"], "1234")
        self.assertEqual(node["integrationType"]["key"], self.ebay_type.key)
        self.assertEqual(node["categories"][0]["code"], "PRODUCT_DATA")

    def test_public_issue_categories_query_orders_by_code(self):
        response = self.strawberry_test_client(query=PUBLIC_ISSUE_CATEGORIES_QUERY)

        self.assertIsNone(response.errors)
        edges = response.data["publicIssueCategories"]["edges"]
        self.assertEqual([edge["node"]["code"] for edge in edges], ["CATALOG", "PRODUCT_DATA"])

    def test_public_issue_query_gets_single_issue_by_id(self):
        response = self.strawberry_test_client(
            query=PUBLIC_ISSUE_QUERY,
            variables={"id": self.to_global_id(self.matching_issue)},
        )

        self.assertIsNone(response.errors)
        node = response.data["publicIssue"]
        self.assertEqual(node["id"], self.to_global_id(self.matching_issue))
        self.assertEqual(node["code"], "1234")
        self.assertEqual(node["recommendedFix"], "Fill the color attribute and retry the listing sync.")
        self.assertTrue(node["images"][0]["imageUrl"].endswith("/issue-image.jpg"))
