from model_bakery import baker
from core.tests import TestCase
from products.models import ProductTranslation
from sales_channels.integrations.shopify.constants import DEFAULT_METAFIELD_NAMESPACE
from sales_channels.integrations.shopify.models.products import ShopifyProduct, ShopifyProductContent
from sales_channels.integrations.shopify.models.sales_channels import ShopifySalesChannel
from sales_channels.integrations.shopify.factories.products import ShopifyProductContentUpdateFactory


class ShopifyProductContentUpdateFactoryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = ShopifySalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shop.test.com",
        )
        self.product = baker.make(
            "products.Product",
            sku="SKU123",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_product = ShopifyProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_id="gid://Shopify/Product/1",
        )
        self.remote_content = ShopifyProductContent.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )
        # Default translation
        self.default_translation = ProductTranslation.objects.create(
            product=self.product,
            sales_channel=None,
            language=self.multi_tenant_company.language,
            name="Default name",
            short_description="Default short",
            description="Default description",
            url_key="default-url",
            multi_tenant_company=self.multi_tenant_company,
        )
        # Channel translation with partial values
        self.channel_translation = ProductTranslation.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            language=self.multi_tenant_company.language,
            name="Channel name",
            description="<p><br></p>",
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_custom_payload_falls_back_to_default_translation(self):
        fac = ShopifyProductContentUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            remote_instance=self.remote_content,
        )
        fac.customize_payload()
        expected = {
            "id": self.remote_product.remote_id,
            "title": "Channel name",
            "descriptionHtml": "Default description",
            "handle": "default-url",
            "metafields": [
                {
                    "namespace": DEFAULT_METAFIELD_NAMESPACE,
                    "key": "short_description",
                    "type": "multi_line_text_field",
                    "value": "Default short",
                }
            ],
        }
        self.assertEqual(fac.payload, expected)
