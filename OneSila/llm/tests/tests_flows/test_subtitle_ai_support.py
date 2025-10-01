from types import SimpleNamespace
from unittest.mock import patch

from core.tests import TestCase
from llm.factories.content import SubtitleLLM
from llm.factories.translations import StringTranslationLLM
from llm.flows.generate_ai_content import AIGenerateContentFlow
from llm.flows.translate_ai_content import AITranslateContentFlow, BulkAiTranslateContentFlow
from llm.schema.types.input import ContentAiGenerateType
from products.models import ProductTranslation, SimpleProduct


def _fake_translate(instance):
    instance.ai_process = SimpleNamespace(transaction=SimpleNamespace(points=1))
    return f"translated-{instance.to_translate}"


def _fake_generate(instance):
    instance.ai_process = SimpleNamespace(
        result="Generated subtitle",
        transaction=SimpleNamespace(points=3),
    )
    return instance.ai_process.result


class SubtitleAiFlowsTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.multi_tenant_company.language = "en"
        self.multi_tenant_company.save()
        self.product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        ProductTranslation.objects.create(
            product=self.product,
            language=self.multi_tenant_company.language,
            name="Rain Coat",
            subtitle="Stay dry in style",
            short_description="Waterproof coat for rainy days",
            description="Long description",
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_ai_translate_flow_supports_subtitle(self):
        with patch.object(StringTranslationLLM, "translate", new=_fake_translate):
            flow = AITranslateContentFlow(
                multi_tenant_company=self.multi_tenant_company,
                to_translate=None,
                from_language_code=self.multi_tenant_company.language,
                to_language_code="nl",
                product=self.product,
                content_type=ContentAiGenerateType.SUBTITLE,
            )

            result = flow.flow()

        self.assertEqual(result, "translated-Stay dry in style")
        self.assertEqual(flow.used_points, 1)

    def test_bulk_translation_updates_subtitle(self):
        with patch.object(StringTranslationLLM, "translate", new=_fake_translate):
            flow = BulkAiTranslateContentFlow(
                multi_tenant_company=self.multi_tenant_company,
                from_language_code=self.multi_tenant_company.language,
                to_language_codes=["nl"],
                products=SimpleProduct.objects.filter(id=self.product.id),
            )
            flow.translate_products()

        translation = ProductTranslation.objects.get(product=self.product, language="nl")
        self.assertEqual(translation.subtitle, "translated-Stay dry in style")
        self.assertEqual(flow.total_points, 4)

    def test_ai_generate_flow_uses_subtitle_factory(self):
        with patch.object(SubtitleLLM, "generate_response", new=_fake_generate):
            flow = AIGenerateContentFlow(
                product=self.product,
                language="nl",
                content_type=ContentAiGenerateType.SUBTITLE,
            )
            content = flow.flow()

        self.assertEqual(content, "Generated subtitle")
        self.assertEqual(flow.used_points, 3)
