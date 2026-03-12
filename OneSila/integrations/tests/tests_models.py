from django.test import TransactionTestCase

from integrations.models import PublicIntegrationType, PublicIntegrationTypeTranslation
from integrations.tests.helpers import PublicIntegrationTypeSchemaMixin


class PublicIntegrationTypeModelTests(PublicIntegrationTypeSchemaMixin, TransactionTestCase):
    def test_name_and_description_use_requested_language_and_fallback(self):
        integration_type = PublicIntegrationType.objects.create(
            key="amazon_model_test",
            type="channel",
            subtype="marketplace",
            category=PublicIntegrationType.CATEGORY_MARKETPLACE,
            active=True,
            is_beta=False,
            supports_open_ai_product_feed=True,
            sort_order=10,
        )
        PublicIntegrationTypeTranslation.objects.create(
            public_integration_type=integration_type,
            language="en",
            name="Amazon",
            description="English description",
        )
        PublicIntegrationTypeTranslation.objects.create(
            public_integration_type=integration_type,
            language="de",
            name="Amazon DE",
            description="",
        )

        self.assertEqual(integration_type.name(language="de"), "Amazon DE")
        self.assertEqual(integration_type.description(language="de"), "English description")
        self.assertEqual(integration_type.name(language="fr"), "Amazon")
        self.assertEqual(integration_type.description(language="fr"), "English description")

    def test_str_falls_back_to_key_when_no_translation_exists(self):
        integration_type = PublicIntegrationType.objects.create(
            key="shopify_model_test",
            type="channel",
            category=PublicIntegrationType.CATEGORY_STOREFRONT,
        )

        self.assertEqual(str(integration_type), "shopify_model_test")
