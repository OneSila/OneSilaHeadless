import json
from types import SimpleNamespace
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
from sales_channels.integrations.amazon.models import AmazonProductBrowseNode
from sales_channels.integrations.amazon.models.properties import AmazonProductType
from sales_channels.integrations.amazon.factories.products import AmazonProductContentUpdateFactory


class AmazonProductContentUpdateFactoryTest(DisableWooCommerceSignalsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER123",
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
            local_instance="en"
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
        self.remote_product.product_owner = True
        self.remote_product.save()
        AmazonProductBrowseNode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel=self.sales_channel,
            view=self.view,
            recommended_browse_node_id="1",
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

    def get_patch_value(self, patches, path):
        for patch in patches:
            if patch["path"] == path:
                return patch["value"]

        return None

    def get_put_and_patch_item_listing_mock_response(self, attributes=None):
        mock_response = MagicMock(spec=["submissionId", "processingStatus", "issues", "status"])
        mock_response.submissionId = "mock-submission-id"
        mock_response.processingStatus = "VALID"
        mock_response.status = "VALID"
        mock_response.issues = []

        if attributes:
            mock_response.attributes = attributes

        return mock_response

    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    def test_update_content_builds_correct_body(self, mock_client, mock_listings):
        mock_instance = mock_listings.return_value
        mock_instance.patch_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()
        mock_instance.get_listings_item.return_value = SimpleNamespace(attributes={})

        fac = AmazonProductContentUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            view=self.view,
            remote_instance=self.remote_content,
        )
        fac.run()

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")
        patches = body.get("patches", [])

        self.assertEqual(body.get("productType"), "CHAIR")

        self.assertIn(
            {
                'op': 'replace',
                'path': '/attributes/item_name',
                'value': [{
                    'value': 'Chair name',
                    'language_tag': 'en',
                    'marketplace_id': 'GB',
                }],
            },
            patches,
        )
        self.assertIn(
            {
                'op': 'replace',
                'path': '/attributes/product_description',
                'value': [{
                    'value': 'Chair description',
                    'language_tag': 'en',
                    'marketplace_id': 'GB',
                }],
            },
            patches,
        )
        self.assertIn(
            {
                'op': 'replace',
                'path': '/attributes/bullet_point',
                'value': [
                    {
                        'value': 'Point one',
                        'language_tag': 'en',
                        'marketplace_id': 'GB',
                    },
                    {
                        'value': 'Point two',
                        'language_tag': 'en',
                        'marketplace_id': 'GB',
                    },
                ],
            },
            patches,
        )

    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    def test_update_content_skips_empty_description(self, mock_client, mock_listings):
        mock_instance = mock_listings.return_value
        mock_instance.patch_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()
        mock_instance.get_listings_item.return_value = SimpleNamespace(attributes={})

        self.translation.description = "<p><br></p>"
        self.translation.save()
        ProductTranslation.objects.create(
            product=self.product,
            sales_channel=None,
            language=self.multi_tenant_company.language,
            name="Default name",
            description="<p><br></p>",
            multi_tenant_company=self.multi_tenant_company,
        )

        fac = AmazonProductContentUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            view=self.view,
            remote_instance=self.remote_content,
        )
        fac.run()

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")
        patches = body.get("patches", [])

        for patch in patches:
            self.assertNotEqual(patch.get("path"), "/attributes/product_description")
