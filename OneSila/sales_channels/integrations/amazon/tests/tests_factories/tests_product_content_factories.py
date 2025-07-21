import json
from unittest.mock import patch, MagicMock

from model_bakery import baker

from core.tests import TestCase
from products.models import ProductTranslation, ProductTranslationBulletPoint
from properties.models import (
    Property,
    PropertyTranslation,
    PropertySelectValue,
    PropertySelectValueTranslation,
    ProductProperty,
    ProductPropertiesRule,
)
from sales_channels.integrations.amazon.tests.helpers import DisableWooCommerceSignalsMixin
from sales_channels.models.sales_channels import SalesChannelViewAssign
from sales_channels.integrations.amazon.models.sales_channels import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonRemoteLanguage,
)
from sales_channels.integrations.amazon.models.products import (
    AmazonProduct,
    AmazonProductContent,
)
from sales_channels.integrations.amazon.models.properties import AmazonProductType
from sales_channels.integrations.amazon.factories.products import AmazonProductContentUpdateFactory


class AmazonProductContentUpdateFactoryTest(DisableWooCommerceSignalsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER123",
            listing_owner=True
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="UK",
            api_region_code="EU_UK",
            remote_id="GB",
        )
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_code="en",
        )

        # Product type property, value and rule
        self.product_type_property = Property.objects.filter(
            is_product_type=True, multi_tenant_company=self.multi_tenant_company
        ).first()
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property,
            language=self.multi_tenant_company.language,
            name="Category",
        )
        self.product_type_value = baker.make(
            PropertySelectValue,
            property=self.product_type_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.product_type_value,
            language=self.multi_tenant_company.language,
            value="Chair",
        )
        self.rule = ProductPropertiesRule.objects.filter(
            product_type=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        ).first()

        # Product
        self.product = baker.make(
            "products.Product",
            sku="TESTSKU",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=self.product,
            property=self.product_type_property,
            value_select=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.translation = ProductTranslation.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            language=self.multi_tenant_company.language,
            name="Chair name",
            description="Chair description",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslationBulletPoint.objects.create(
            product_translation=self.translation,
            multi_tenant_company=self.multi_tenant_company,
            text="Point one",
            sort_order=0,
        )
        ProductTranslationBulletPoint.objects.create(
            product_translation=self.translation,
            multi_tenant_company=self.multi_tenant_company,
            text="Point two",
            sort_order=1,
        )

        # Remote product and assignment
        self.remote_product = AmazonProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="AMZSKU",
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel_view=self.view,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )

        # Mapping
        self.amazon_product_type = AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.rule,
            product_type_code="CHAIR",
        )

        self.remote_content = AmazonProductContent.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )

    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    def test_update_content_builds_correct_body(self, mock_client, mock_listings):
        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.side_effect = Exception("no amazon")
        mock_instance.get_listings_item.return_value = MagicMock(payload={"attributes": {}})

        fac = AmazonProductContentUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            view=self.view,
            remote_instance=self.remote_content,
        )

        with self.assertRaises(Exception):
            fac.run()

        expected_body = {
            "productType": "CHAIR",
            "requirements": "LISTING",
            "attributes": {
                "item_name": [{"value": "Chair name"}],
                "product_description": [{"value": "Chair description"}],
                "bullet_point": [
                    {"value": "Point one"},
                    {"value": "Point two"},
                ],
            },
        }

        body = mock_instance.put_listings_item.call_args.kwargs.get("body")
        self.assertEqual(body, expected_body)
