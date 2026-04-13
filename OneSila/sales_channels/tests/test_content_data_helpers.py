from core.tests import TestCase
from products.models import Product, ProductTranslation, ProductTranslationBulletPoint
from sales_channels.helpers import build_content_data
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
    ) -> ProductTranslation:
        return ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            sales_channel=sales_channel,
            language=language,
            name=name,
            subtitle=subtitle,
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
                    "bulletPoints": ["Default bullet 1", "Default bullet 2"],
                }
            },
        )
