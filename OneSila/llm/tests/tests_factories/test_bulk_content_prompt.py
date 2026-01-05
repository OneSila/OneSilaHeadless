import json

from core.tests import TestCase
from integrations.constants import EBAY_INTEGRATION
from llm.factories.bulk_content import BulkContentLLM, INTEGRATION_GUIDELINES, build_field_rules
from products.models import SimpleProduct
from sales_channels.integrations.ebay.models import EbaySalesChannel


class BulkContentLLMPromptTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.multi_tenant_company.language = "en"
        self.multi_tenant_company.save()

        self.product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="TEST-PROMPT",
        )
        self.sales_channel = EbaySalesChannel.objects.create(
            hostname="ebay-prompt",
            multi_tenant_company=self.multi_tenant_company,
        )

    def _build_llm(
        self,
        *,
        additional_informations: str | None,
        product_context: dict | None = None,
    ) -> BulkContentLLM:
        product_context = product_context or {}
        channel = {
            "integration_id": self.sales_channel.global_id,
            "integration_fallback_id": str(self.sales_channel.id),
            "integration_type": EBAY_INTEGRATION,
            "languages": ["en"],
            "default_language": "en",
            "field_rules": build_field_rules(integration_type=EBAY_INTEGRATION),
            "product_context": product_context,
            "integration_guidelines": INTEGRATION_GUIDELINES.get(EBAY_INTEGRATION, []),
        }
        return BulkContentLLM(
            product=self.product,
            channels=[channel],
            additional_informations=additional_informations,
            debug=False,
        )

    def test_additional_informations_appended_to_prompt(self):
        llm = self._build_llm(additional_informations="Focus on durability and warranty details.")
        payload = json.loads(llm.prompt)

        self.assertEqual(list(payload.keys())[-1], "additional_informations")
        self.assertEqual(payload["additional_informations"], "Focus on durability and warranty details.")

    def test_additional_informations_omitted_when_blank(self):
        llm = self._build_llm(additional_informations="   ")
        payload = json.loads(llm.prompt)

        self.assertNotIn("additional_informations", payload)

    def test_prompt_excludes_existing_content(self):
        llm = self._build_llm(additional_informations=None)
        payload = json.loads(llm.prompt)

        self.assertNotIn("existing_content", payload["channels"][0])

    def test_system_prompt_excludes_url_key(self):
        llm = self._build_llm(additional_informations=None)

        self.assertNotIn("urlKey", llm.system_prompt)
        self.assertNotIn("existing_content", llm.system_prompt)
        self.assertIn("len(value)", llm.system_prompt)
        self.assertNotIn("80%", llm.system_prompt)

    def test_system_prompt_enforces_language_output(self):
        llm = self._build_llm(additional_informations=None)

        self.assertIn("never output English for non-English codes", llm.system_prompt)

    def test_prompt_includes_writing_brief(self):
        llm = self._build_llm(additional_informations=None)
        payload = json.loads(llm.prompt)

        self.assertIn("writing_brief", payload)
        self.assertTrue(payload["writing_brief"])

    def test_images_from_product_context(self):
        llm = self._build_llm(
            additional_informations=None,
            product_context={
                "media": {
                    "images": ["https://example.com/image.jpg"],
                    "documents": [],
                }
            },
        )

        self.assertEqual(llm.images, ["https://example.com/image.jpg"])
