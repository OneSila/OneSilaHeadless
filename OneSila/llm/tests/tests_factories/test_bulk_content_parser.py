import json
from types import SimpleNamespace
from unittest.mock import patch

from core.tests import TestCase
from integrations.constants import EBAY_INTEGRATION
from llm.factories.bulk_content import BulkContentLLM, INTEGRATION_GUIDELINES, build_field_rules
from products.models import SimpleProduct
from sales_channels.integrations.ebay.models import EbaySalesChannel


class BulkContentLLMParserTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.multi_tenant_company.language = "en"
        self.multi_tenant_company.save()

        self.product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="TEST-PARSER",
        )
        self.sales_channel = EbaySalesChannel.objects.create(
            hostname="ebay-parser",
            multi_tenant_company=self.multi_tenant_company,
        )

    def _build_llm(self) -> BulkContentLLM:
        channel = {
            "integration_id": self.sales_channel.global_id,
            "integration_fallback_id": str(self.sales_channel.id),
            "integration_type": EBAY_INTEGRATION,
            "languages": ["en"],
            "default_language": "en",
            "field_rules": build_field_rules(integration_type=EBAY_INTEGRATION),
            "product_context": {},
            "integration_guidelines": INTEGRATION_GUIDELINES.get(EBAY_INTEGRATION, []),
        }
        return BulkContentLLM(
            product=self.product,
            channels=[channel],
            additional_informations=None,
            debug=False,
        )

    def test_clean_json_response_repairs_unterminated_string(self):
        llm = self._build_llm()
        text = "{\"foo\": {\"bar\": \"Kids Crocodile"

        payload = llm._clean_json_response(text=text)

        self.assertEqual(payload, {"foo": {"bar": "Kids Crocodile"}})

    def test_clean_json_response_unescapes_apostrophes(self):
        llm = self._build_llm()
        text = "{\"foo\": \"Children\\'s costume\"}"

        payload = llm._clean_json_response(text=text)

        self.assertEqual(payload["foo"], "Children's costume")

    def test_generate_content_logs_validation_errors(self):
        llm = self._build_llm()
        response_text = json.dumps(
            {
                self.sales_channel.global_id: {
                    llm.product_sku: {
                        "en": {"name": "Name only"},
                    }
                }
            },
            ensure_ascii=True,
        )
        dummy_response = SimpleNamespace(
            usage=SimpleNamespace(
                input_tokens=1,
                output_tokens=1,
                input_tokens_details=SimpleNamespace(cached_tokens=0),
            ),
            output_text=response_text,
        )

        with patch.object(BulkContentLLM, "ask_gpt", return_value=dummy_response):
            with self.assertLogs("llm.factories.bulk_content", level="WARNING") as logs:
                payload = llm.generate_content()

        self.assertIn("BulkContentLLM validation errors", "\n".join(logs.output))
        self.assertIn(self.sales_channel.global_id, payload)
