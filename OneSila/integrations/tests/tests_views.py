from django.core.files.base import ContentFile
from django.test import TransactionTestCase

from integrations.models import PublicIntegrationType, PublicIntegrationTypeTranslation
from integrations.tests.helpers import PublicIntegrationTypeSchemaMixin
from media.tests.helpers import CreateImageMixin


class PublicIntegrationTypeDirectViewTests(
    CreateImageMixin,
    PublicIntegrationTypeSchemaMixin,
    TransactionTestCase,
):
    def setUp(self):
        super().setUp()
        self.integration_type = PublicIntegrationType.objects.create(
            key="rest_shopify_test",
            type="shopify",
            category=PublicIntegrationType.CATEGORY_STOREFRONT,
            active=True,
            supports_open_ai_product_feed=True,
            sort_order=9991,
        )
        PublicIntegrationTypeTranslation.objects.create(
            public_integration_type=self.integration_type,
            language="en",
            name="REST Shopify",
            description="REST description",
        )
        self.integration_type.logo_png.save("rest-shopify.png", self.get_image_file("red.png"), save=True)
        self.integration_type.logo_svg.save(
            "rest-shopify.svg",
            ContentFile(b"<svg xmlns='http://www.w3.org/2000/svg'></svg>"),
            save=True,
        )

        self.inactive_integration_type = PublicIntegrationType.objects.create(
            key="rest_inactive_test",
            type="shopify",
            category=PublicIntegrationType.CATEGORY_STOREFRONT,
            active=False,
            sort_order=9992,
        )
        PublicIntegrationTypeTranslation.objects.create(
            public_integration_type=self.inactive_integration_type,
            language="en",
            name="REST Inactive",
            description="Should be filtered out",
        )

    def test_direct_integrations_endpoint_supports_filters_and_absolute_logo_urls(self):
        response = self.client.get(
            "/direct/integrations/",
            {
                "key": self.integration_type.key,
                "active": "",
                "language": "en",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 1)
        result = payload["results"][0]
        self.assertEqual(result["key"], self.integration_type.key)
        self.assertEqual(result["name"], "REST Shopify")
        self.assertEqual(result["description"], "REST description")
        self.assertTrue(result["logo_png"].startswith("http"))
        self.assertTrue(result["logo_svg"].startswith("http"))
        self.assertTrue(result["logo_png"].endswith("rest-shopify.png"))
        self.assertTrue(result["logo_svg"].endswith("rest-shopify.svg"))
