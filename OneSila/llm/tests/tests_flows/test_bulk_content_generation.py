from unittest.mock import patch

from core.tests import TestCase
from llm.factories.bulk_content import BulkContentLLM
from llm.flows.bulk_generate_content import BulkGenerateContentFlow
from products.models import ProductTranslation, ProductTranslationBulletPoint, SimpleProduct
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.integrations.ebay.models import EbaySalesChannel


class BulkContentGenerationFlowTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.multi_tenant_company.language = "en"
        self.multi_tenant_company.save()

        self.product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="TEST-123",
        )
        ProductTranslation.objects.create(
            product=self.product,
            language="en",
            name="Existing Name",
            short_description="<p>Existing short</p>",
            description="<p>Existing description</p>",
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_preview_bulk_generation_returns_payload(self):
        sales_channel = EbaySalesChannel.objects.create(
            hostname="ebay-test",
            multi_tenant_company=self.multi_tenant_company,
        )
        integration_id = sales_channel.global_id

        def _fake_generate(self, *, max_attempts: int = 2):
            self.used_points = 5
            return {
                integration_id: {
                    "en": {
                        "name": "Generated Name",
                        "subtitle": "Generated Subtitle",
                        "shortDescription": "<p>Generated short</p>",
                        "description": "<p>Generated description</p>",
                    }
                }
            }

        with patch.object(BulkContentLLM, "generate_content", new=_fake_generate):
            flow = BulkGenerateContentFlow(
                multi_tenant_company=self.multi_tenant_company,
                product_ids=[self.product.id],
                sales_channel_languages={sales_channel.id: ["en"]},
                sales_channel_defaults={sales_channel.id: "en"},
                override=True,
                preview=True,
            )
            payload = flow.flow()

        content = payload[0][sales_channel.global_id][str(self.product.sku)]["en"]
        self.assertEqual(content["name"], "Generated Name")
        self.assertEqual(flow.used_points, 5)

    def test_non_override_adds_missing_bullet_points(self):
        sales_channel = AmazonSalesChannel.objects.create(
            hostname="amazon-test",
            multi_tenant_company=self.multi_tenant_company,
        )
        integration_id = sales_channel.global_id
        def _fake_generate(self, *, max_attempts: int = 2):
            self.used_points = 3
            return {
                integration_id: {
                    "en": {
                        "name": "Generated Name",
                        "description": "<p>Generated description</p>",
                        "bulletPoints": ["Point A", "Point B", "Point C", "Point D", "Point E"],
                    }
                }
            }
        translation = ProductTranslation.objects.create(
            product=self.product,
            language="en",
            sales_channel=sales_channel,
            name="Amazon Name",
            description="<p>Amazon description</p>",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslationBulletPoint.objects.bulk_create(
            [
                ProductTranslationBulletPoint(product_translation=translation, text="Point A", sort_order=0),
                ProductTranslationBulletPoint(product_translation=translation, text="Point B", sort_order=1),
                ProductTranslationBulletPoint(product_translation=translation, text="Point C", sort_order=2),
            ]
        )

        with patch.object(BulkContentLLM, "generate_content", new=_fake_generate):
            flow = BulkGenerateContentFlow(
                multi_tenant_company=self.multi_tenant_company,
                product_ids=[self.product.id],
                sales_channel_languages={sales_channel.id: ["en"]},
                sales_channel_defaults={sales_channel.id: "en"},
                override=False,
                preview=False,
            )
            flow.flow()

        translation.refresh_from_db()
        bullet_points = list(translation.bullet_points.order_by("sort_order").values_list("text", flat=True))
        self.assertEqual(translation.name, "Amazon Name")
        self.assertEqual(bullet_points, ["Point A", "Point B", "Point C", "Point D", "Point E"])

    def test_preview_bulk_generation_supports_default_channel(self):
        def _fake_generate(self, *, max_attempts: int = 2):
            self.used_points = 2
            return {
                "default": {
                    "en": {
                        "name": "Generated Name",
                    }
                }
            }

        with patch.object(BulkContentLLM, "generate_content", new=_fake_generate):
            flow = BulkGenerateContentFlow(
                multi_tenant_company=self.multi_tenant_company,
                product_ids=[self.product.id],
                sales_channel_languages={"default": ["en"]},
                sales_channel_defaults={"default": "en"},
                override=True,
                preview=True,
            )
            payload = flow.flow()

        content = payload[0]["default"][str(self.product.sku)]["en"]
        self.assertEqual(content["name"], "Generated Name")
        self.assertEqual(flow.used_points, 2)
