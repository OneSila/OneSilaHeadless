from unittest.mock import patch

from model_bakery import baker

from core.tests import TestCase
from media.models import Media, MediaProductThrough
from properties.models import Property, ProductProperty, PropertySelectValue
from products.models import ProductTranslation, ProductTranslationBulletPoint
from sales_channels.exceptions import MissingMappingError, PreFlightCheckError
from sales_channels.integrations.mirakl.factories.feeds.product_payloads import MiraklProductPayloadBuilder
from sales_channels.integrations.mirakl.models import (
    MiraklProduct,
    MiraklProductCategory,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertyApplicability,
    MiraklSalesChannel,
    MiraklSalesChannelView,
)


class MiraklProductPayloadBuilderTests(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )
        self.view = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="default-view",
        )

    def _build_builder(
        self,
        *,
        remote_code: str,
        local_property: Property,
        required: bool,
        remote_type: str = "TEXT",
    ) -> tuple[MiraklProductPayloadBuilder, MiraklProperty, object]:
        product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
            sku="SKU-1",
        )
        remote_product = baker.make(
            MiraklProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product,
        )
        product_type = baker.make(
            MiraklProductType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="cat-1",
        )
        baker.make(
            MiraklProductCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=product,
            remote_id="cat-1",
        )
        remote_property = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code=remote_code,
            type=remote_type,
            local_instance=local_property,
        )
        baker.make(
            MiraklPropertyApplicability,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            property=remote_property,
            view=self.view,
        )
        baker.make(
            MiraklProductTypeItem,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type=product_type,
            remote_property=remote_property,
            required=required,
        )
        return (
            MiraklProductPayloadBuilder(
                remote_product=remote_product,
                sales_channel_view=self.view,
            ),
            remote_property,
            product,
        )

    def test_optional_mapped_field_without_product_value_builds_blank_value(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, _, _ = self._build_builder(
            remote_code="collection",
            local_property=local_property,
            required=False,
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["collection"], "")

    def test_required_mapped_field_without_product_value_raises_missing_value_error(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
            internal_name="collection_local",
        )
        builder, _, _ = self._build_builder(
            remote_code="collection",
            local_property=local_property,
            required=True,
        )

        with self.assertRaisesMessage(
            PreFlightCheckError,
            "Mirakl preflight errors:\n- Mirakl required property 'collection' (local 'collection_local') has no value for product SKU-1.",
        ):
            builder.build()

    def test_required_representation_field_without_local_property_keeps_generic_message(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, _ = self._build_builder(
            remote_code="ean",
            local_property=local_property,
            required=True,
        )
        remote_property.local_instance = None
        remote_property.representation_type = remote_property.REPRESENTATION_PRODUCT_EAN
        remote_property.save()

        with self.assertRaisesMessage(
            PreFlightCheckError,
            "Mirakl preflight errors:\n- Mirakl required field 'ean' is missing for product SKU-1.",
        ):
            builder.build()

    def test_required_mapped_field_for_variation_mentions_variation_product(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
            internal_name="style",
        )
        builder, remote_property, product = self._build_builder(
            remote_code="style_suits",
            local_property=local_property,
            required=True,
        )
        parent_product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="CONFIGURABLE",
            sku="PARENT-1",
        )
        message = builder._build_missing_required_value_message(
            remote_property=remote_property,
            product_context={
                "product": product,
                "parent_product": parent_product,
                "sku": "SKU-1",
            },
        )

        self.assertEqual(
            message,
            "Mirakl required property 'style_suits' (local 'style') has no value for variation product SKU-1.",
        )

    def test_select_field_with_unmapped_local_value_still_raises_missing_mapping(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        builder, _, product = self._build_builder(
            remote_code="colour",
            local_property=local_property,
            required=True,
            remote_type="SELECT",
        )
        local_select_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=local_property,
        )
        baker.make(
            ProductProperty,
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=local_property,
            value_select=local_select_value,
        )

        with self.assertRaisesMessage(
            MissingMappingError,
            "Missing Mirakl mappings:\n- Map the OneSila select value for Mirakl field 'colour' before pushing.",
        ):
            builder.build()

    @patch("media.models.Media.image_url", return_value="https://cdn.example.com/color.jpg")
    def test_required_swatch_uses_color_image_media(self, _image_url_mock):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, product = self._build_builder(
            remote_code="swatch",
            local_property=local_property,
            required=True,
        )
        remote_property.local_instance = None
        remote_property.representation_type = remote_property.REPRESENTATION_SWATCH_IMAGE
        remote_property.save()
        media = baker.make(
            Media,
            multi_tenant_company=self.multi_tenant_company,
            type=Media.IMAGE,
            image_type=Media.COLOR_SHOT,
        )
        baker.make(
            MediaProductThrough,
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            media=media,
            is_main_image=False,
            sales_channel=None,
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["swatch"], "https://cdn.example.com/color.jpg")

    def test_empty_rich_text_translation_is_treated_as_blank(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, _, product = self._build_builder(
            remote_code="collection",
            local_property=local_property,
            required=False,
        )
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            language=self.multi_tenant_company.language,
            sales_channel=None,
            name="Test product",
            short_description="<p><br></p>",
            description="<p><br></p>",
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["internal-description"], "")
        self.assertEqual(rows[0]["description"], "")

    def test_bullet_point_representation_uses_shared_content_bullet_points(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, product = self._build_builder(
            remote_code="bullet_1",
            local_property=local_property,
            required=False,
        )
        remote_property.local_instance = None
        remote_property.representation_type = remote_property.REPRESENTATION_PRODUCT_BULLET_POINT
        remote_property.save()
        translation = ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            language=self.multi_tenant_company.language,
            sales_channel=None,
            name="Test product",
            short_description="<p><br></p>",
            description="<p><br></p>",
        )
        ProductTranslationBulletPoint.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_translation=translation,
            text="First shared bullet",
            sort_order=0,
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["bullet_1"], "First shared bullet")
