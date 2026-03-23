from unittest.mock import patch
from datetime import date

from eancodes.models import EanCode
from model_bakery import baker

from core.tests import TestCase
from media.models import Media, MediaProductThrough
from products.models import ConfigurableVariation
from properties.models import Property, ProductProperty, PropertySelectValue
from products.models import ProductTranslation, ProductTranslationBulletPoint
from sales_channels.exceptions import MiraklPayloadValidationError, MissingMappingError, PreFlightCheckError
from sales_channels.integrations.mirakl.factories.feeds.product_payloads import MiraklProductPayloadBuilder
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklProduct,
    MiraklProductCategory,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertyApplicability,
    MiraklPropertySelectValue,
    MiraklSalesChannel,
    MiraklSalesChannelView,
)
from sales_channels.models import SalesChannelFeedItem
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklProductPayloadBuilderTests(DisableMiraklConnectionMixin, TestCase):
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
        action: str = SalesChannelFeedItem.ACTION_UPDATE,
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
        category = baker.make(
            MiraklCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="cat-1",
            name="Category 1",
            is_leaf=True,
        )
        product_type = baker.make(
            MiraklProductType,
            category=category,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=None,
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
                action=action,
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

    def test_select_field_uses_mapped_remote_code_in_payload(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        builder, remote_property, product = self._build_builder(
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
        baker.make(
            MiraklPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=remote_property,
            local_instance=local_select_value,
            code="PURPLE_CODE",
            value="Purple Label",
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["colour"], "PURPLE_CODE")

    def test_multiselect_field_uses_mapped_remote_codes_in_payload(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.MULTISELECT,
        )
        builder, remote_property, product = self._build_builder(
            remote_code="materials",
            local_property=local_property,
            required=True,
            remote_type="MULTISELECT",
        )
        first_local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=local_property,
        )
        second_local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=local_property,
        )
        product_property = baker.make(
            ProductProperty,
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=local_property,
        )
        product_property.value_multi_select.add(first_local_value, second_local_value)
        baker.make(
            MiraklPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=remote_property,
            local_instance=first_local_value,
            code="COTTON_CODE",
            value="Cotton",
        )
        baker.make(
            MiraklPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=remote_property,
            local_instance=second_local_value,
            code="LINEN_CODE",
            value="Linen",
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["materials"], "COTTON_CODE,LINEN_CODE")

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

    @patch("media.models.Media.image_url", return_value="https://cdn.example.com/parent.jpg")
    def test_configurable_variations_reuse_parent_content_and_images(self, _image_url_mock):
        parent_product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="CONFIGURABLE",
            sku="PARENT-1",
        )
        child_product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
            sku="CHILD-1",
        )
        baker.make(
            ConfigurableVariation,
            multi_tenant_company=self.multi_tenant_company,
            parent=parent_product,
            variation=child_product,
        )
        remote_product = baker.make(
            MiraklProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent_product,
        )
        category = baker.make(
            MiraklCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="cat-1",
            name="Category 1",
            is_leaf=True,
        )
        product_type = baker.make(
            MiraklProductType,
            category=category,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=None,
            remote_id="cat-1",
        )
        baker.make(
            MiraklProductCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=child_product,
            remote_id="cat-1",
        )
        title_property = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="title_field",
            local_instance=None,
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_TITLE,
        )
        image_property = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="main_image",
            local_instance=None,
            representation_type=MiraklProperty.REPRESENTATION_THUMBNAIL_IMAGE,
        )
        for remote_property in (title_property, image_property):
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
                required=False,
            )
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=parent_product,
            language=self.multi_tenant_company.language,
            sales_channel=None,
            name="Parent Name",
            short_description="Parent short",
            description="Parent description",
        )
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=child_product,
            language=self.multi_tenant_company.language,
            sales_channel=None,
            name="Child Name",
            short_description="Child short",
            description="Child description",
        )
        media = baker.make(
            Media,
            multi_tenant_company=self.multi_tenant_company,
            type=Media.IMAGE,
            image_type=Media.PACK_SHOT,
        )
        baker.make(
            MediaProductThrough,
            multi_tenant_company=self.multi_tenant_company,
            product=parent_product,
            media=media,
            is_main_image=True,
            sales_channel=None,
        )

        _, rows = MiraklProductPayloadBuilder(
            remote_product=remote_product,
            sales_channel_view=self.view,
        ).build()

        self.assertEqual(rows[0]["title_field"], "Parent Name")
        self.assertEqual(rows[0]["main_image"], "https://cdn.example.com/parent.jpg")

    def test_optional_configurable_sku_representation_stays_empty_for_standalone_product(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, _ = self._build_builder(
            remote_code="parent_sku",
            local_property=local_property,
            required=False,
        )
        remote_property.local_instance = None
        remote_property.representation_type = remote_property.REPRESENTATION_PRODUCT_CONFIGURABLE_SKU
        remote_property.save()

        _, rows = builder.build()

        self.assertEqual(rows[0]["parent_sku"], "")

    def test_required_configurable_sku_representation_uses_standalone_product_sku(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, _ = self._build_builder(
            remote_code="parent_sku",
            local_property=local_property,
            required=True,
        )
        remote_property.local_instance = None
        remote_property.representation_type = remote_property.REPRESENTATION_PRODUCT_CONFIGURABLE_SKU
        remote_property.save()

        _, rows = builder.build()

        self.assertEqual(rows[0]["parent_sku"], "SKU-1")

    def test_required_configurable_id_representation_uses_standalone_product_id(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, product = self._build_builder(
            remote_code="parent_product_id",
            local_property=local_property,
            required=True,
        )
        remote_property.local_instance = None
        remote_property.representation_type = remote_property.REPRESENTATION_PRODUCT_CONFIGURABLE_ID
        remote_property.save()

        _, rows = builder.build()

        self.assertEqual(rows[0]["parent_product_id"], str(product.id))

    def test_delete_action_uses_placeholder_for_missing_required_text(self):
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
            action=SalesChannelFeedItem.ACTION_DELETE,
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["collection"], "TO_BE_DELETED")

    def test_product_reference_validator_raises_custom_error(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, product = self._build_builder(
            remote_code="ean",
            local_property=local_property,
            required=True,
        )
        remote_property.local_instance = None
        remote_property.representation_type = remote_property.REPRESENTATION_PRODUCT_EAN
        remote_property.validations = ["PRODUCT_REFERENCE|EAN-13"]
        remote_property.save()
        baker.make(
            EanCode,
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            ean_code="123",
        )

        with self.assertRaises(MiraklPayloadValidationError):
            builder._apply_remote_validations(
                remote_property=remote_property,
                value="123",
                product_context={"sku": "SKU-1"},
            )

    def test_delete_action_builds_minimal_product_reference_placeholder(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, _ = self._build_builder(
            remote_code="ean",
            local_property=local_property,
            required=True,
            action=SalesChannelFeedItem.ACTION_DELETE,
        )
        remote_property.local_instance = None
        remote_property.representation_type = remote_property.REPRESENTATION_PRODUCT_EAN
        remote_property.validations = ["PRODUCT_REFERENCE|EAN-8|UPC|EAN-13"]
        remote_property.save()

        _, rows = builder.build()

        self.assertEqual(rows[0]["ean"], "00000000")

    def test_forbidden_words_validator_reports_matching_word(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, _ = self._build_builder(
            remote_code="product_title",
            local_property=local_property,
            required=True,
        )
        remote_property.validations = ['FORBIDDEN_WORDS|"scarface,mob"']
        remote_property.save()

        with self.assertRaisesMessage(
            MiraklPayloadValidationError,
            "Mirakl field 'product_title' contains forbidden word 'scarface' for product SKU-1.",
        ):
            builder._apply_remote_validations(
                remote_property=remote_property,
                value="Scarface costume set",
                product_context={"sku": "SKU-1"},
            )

    def test_forbidden_words_validator_does_not_match_inside_larger_word(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, _ = self._build_builder(
            remote_code="long_description",
            local_property=local_property,
            required=True,
        )
        remote_property.validations = ['FORBIDDEN_WORDS|"eco"']
        remote_property.save()

        value = "The weave type is recorded as test and should not trigger eco."
        with self.assertRaisesMessage(
            MiraklPayloadValidationError,
            "Mirakl field 'long_description' contains forbidden word 'eco' for product SKU-1.",
        ):
            builder._apply_remote_validations(
                remote_property=remote_property,
                value=value,
                product_context={"sku": "SKU-1"},
            )

        clean_value = "The weave type is recorded as test and should not trigger."
        self.assertEqual(
            builder._apply_remote_validations(
                remote_property=remote_property,
                value=clean_value,
                product_context={"sku": "SKU-1"},
            ),
            clean_value,
        )

    def test_precision_type_parameter_truncates_numeric_value(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.FLOAT,
        )
        builder, remote_property, product = self._build_builder(
            remote_code="package_length",
            local_property=local_property,
            required=True,
            remote_type=Property.TYPES.FLOAT,
        )
        remote_property.type_parameters = [{"name": "PRECISION", "value": "2"}]
        remote_property.save(update_fields=["type_parameters"])
        baker.make(
            ProductProperty,
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=local_property,
            value_float=12.349,
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["package_length"], "12.34")

    def test_date_pattern_type_parameter_formats_date_value(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.DATE,
        )
        builder, remote_property, product = self._build_builder(
            remote_code="release_date",
            local_property=local_property,
            required=True,
            remote_type="DATE",
        )
        remote_property.type_parameters = [{"name": "PATTERN", "value": "dd/MM/yyyy"}]
        remote_property.save(update_fields=["type_parameters"])
        baker.make(
            ProductProperty,
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=local_property,
            value_date=date(2026, 3, 17),
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["release_date"], "17/03/2026")
