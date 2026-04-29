from core.tests import TestCase
from products.models import Product, ProductTranslation, ProductTranslationBulletPoint
from sales_channels.exceptions import PreFlightCheckError
from sales_channels.helpers import build_content_data, build_content_payload, select_content_payload
from sales_channels.integrations.amazon.models import (
    AmazonRemoteLanguage,
    AmazonSalesChannel,
    AmazonSalesChannelView,
)
from sales_channels.integrations.ebay.models import (
    EbayRemoteLanguage,
    EbaySalesChannel,
    EbaySalesChannelView,
)
from sales_channels.tests.helpers import DisableMagentoAndWooConnectionsMixin


class BuildContentDataHelperTests(DisableMagentoAndWooConnectionsMixin, TestCase):
    def _create_product(self, *, sku: str) -> Product:
        return Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku=sku,
        )

    def _create_translation(
        self,
        *,
        product: Product,
        sales_channel,
        language: str,
        name: str,
        subtitle: str | None = None,
        description: str | None = None,
        url_key: str | None = None,
    ) -> ProductTranslation:
        return ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            sales_channel=sales_channel,
            language=language,
            name=name,
            subtitle=subtitle,
            description=description,
            url_key=url_key,
        )

    def test_build_content_data_uses_default_subtitle_when_channel_subtitle_missing(self):
        sales_channel = EbaySalesChannel.objects.create(
            hostname="https://ebay.example.com",
            environment=EbaySalesChannel.PRODUCTION,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            remote_id="EBAY_GB",
            name="Great Britain",
        )
        EbayRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            sales_channel_view=view,
            local_instance="en-gb",
            remote_code="en-GB",
        )

        product = self._create_product(sku="CONTENT-DEFAULT-SUBTITLE")
        self._create_translation(
            product=product,
            sales_channel=None,
            language="en-gb",
            name="Default name",
            subtitle="Default subtitle",
        )
        self._create_translation(
            product=product,
            sales_channel=sales_channel,
            language="en-gb",
            name="Channel name",
            subtitle="",
        )

        content_data = build_content_data(product=product, sales_channel=sales_channel)

        self.assertEqual(
            content_data,
            {
                "en-gb": {
                    "name": "Channel name",
                    "subtitle": "Default subtitle",
                    "urlKey": "default-name",
                }
            },
        )

    def test_build_content_data_uses_default_bullet_points_when_channel_bullet_points_missing(self):
        sales_channel = AmazonSalesChannel.objects.create(
            hostname="https://amazon.example.com",
            remote_id="SELLER-123",
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            remote_id="GB",
            name="United Kingdom",
            api_region_code="EU_UK",
        )
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            sales_channel_view=view,
            local_instance="en-gb",
            remote_code="en",
        )

        product = self._create_product(sku="CONTENT-DEFAULT-BULLETS")
        default_translation = self._create_translation(
            product=product,
            sales_channel=None,
            language="en-gb",
            name="Default name",
        )
        ProductTranslationBulletPoint.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_translation=default_translation,
            text="Default bullet 1",
            sort_order=0,
        )
        ProductTranslationBulletPoint.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_translation=default_translation,
            text="Default bullet 2",
            sort_order=1,
        )
        self._create_translation(
            product=product,
            sales_channel=sales_channel,
            language="en-gb",
            name="Channel name",
        )

        content_data = build_content_data(product=product, sales_channel=sales_channel)

        self.assertEqual(
            content_data,
            {
                "en-gb": {
                    "name": "Channel name",
                    "urlKey": "default-name",
                    "bulletPoints": ["Default bullet 1", "Default bullet 2"],
                }
            },
        )

    def test_build_content_data_includes_url_key_with_channel_fallback(self):
        sales_channel = EbaySalesChannel.objects.create(
            hostname="https://ebay-url.example.com",
            environment=EbaySalesChannel.PRODUCTION,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            remote_id="EBAY_US",
            name="United States",
        )
        EbayRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            sales_channel_view=view,
            local_instance="en",
            remote_code="en-US",
        )

        product = self._create_product(sku="CONTENT-URL-KEY")
        self._create_translation(
            product=product,
            sales_channel=None,
            language="en",
            name="Default URL Name",
            url_key="default-url-key",
        )
        self._create_translation(
            product=product,
            sales_channel=sales_channel,
            language="en",
            name="Channel URL Name",
            url_key="",
        )

        content_data = build_content_data(product=product, sales_channel=sales_channel)

        self.assertEqual(content_data["en"]["urlKey"], "default-url-key")

    def test_select_content_payload_uses_requested_language_then_fallback_then_first_payload(self):
        content_data = {
            "en": {"name": "English name"},
            "fr": {"name": "French name"},
        }

        self.assertEqual(
            select_content_payload(
                content_data=content_data,
                language="fr",
                fallback_language="en",
            ),
            {"name": "French name"},
        )
        self.assertEqual(
            select_content_payload(
                content_data=content_data,
                language="de",
                fallback_language="en",
            ),
            {"name": "English name"},
        )
        self.assertEqual(
            select_content_payload(
                content_data=content_data,
                language="de",
                fallback_language="it",
            ),
            {"name": "English name"},
        )

    def test_build_content_payload_uses_company_language_as_fallback(self):
        sales_channel = EbaySalesChannel.objects.create(
            hostname="https://ebay-payload.example.com",
            environment=EbaySalesChannel.PRODUCTION,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

        self.multi_tenant_company.language = "en"
        self.multi_tenant_company.save(update_fields=["language"])

        payload = build_content_payload(
            product=self._create_product(sku="CONTENT-PAYLOAD-FALLBACK"),
            sales_channel=sales_channel,
            language="de",
            content_data={
                "en": {"name": "English fallback"},
                "fr": {"name": "French fallback"},
            },
        )

        self.assertEqual(payload, {"name": "English fallback"})

    def test_build_content_data_can_validate_sales_channel_minimum_lengths(self):
        sales_channel = EbaySalesChannel.objects.create(
            hostname="https://ebay-validation.example.com",
            environment=EbaySalesChannel.PRODUCTION,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            min_name_length=10,
            min_description_length=20,
        )
        view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            remote_id="EBAY_AU",
            name="Australia",
        )
        EbayRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            sales_channel_view=view,
            local_instance="en",
            remote_code="en-AU",
        )

        product = self._create_product(sku="CONTENT-VALIDATION")
        self._create_translation(
            product=product,
            sales_channel=None,
            language="en",
            name="Short",
            description="Long enough description value",
        )

        with self.assertRaises(PreFlightCheckError):
            build_content_data(
                product=product,
                sales_channel=sales_channel,
                apply_validations=True,
            )
