from unittest.mock import patch
from datetime import date

from django.test import override_settings
from eancodes.models import EanCode
from model_bakery import baker

from core.tests import TestCase
from media.models import DocumentType, Media, MediaProductThrough
from products.models import ConfigurableVariation
from properties.models import Property, ProductProperty, PropertySelectValue
from properties.models import ProductPropertiesRule, PropertySelectValueTranslation, PropertyTranslation
from properties.models import ProductPropertyTextTranslation
from products.models import ProductTranslation, ProductTranslationBulletPoint
from sales_channels.exceptions import MiraklPayloadValidationError, MissingMappingError, PreFlightCheckError, SwitchedToSyncException
from sales_channels.integrations.mirakl.factories.feeds.product_payloads import (
    MiraklProductCreateFactory,
    MiraklProductPayloadBuilder,
)
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklDocumentType,
    MiraklProduct,
    MiraklProductCategory,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertyApplicability,
    MiraklPropertySelectValue,
    MiraklRemoteLanguage,
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

    def test_payload_validation_errors_are_registered_as_sales_channel_user_errors(self):
        self.assertIn(MiraklPayloadValidationError, self.sales_channel._meta.user_exceptions)

    def _assign_product_rule(self, *, product, sales_channel=None):
        product_type_property = Property.objects.get(
            type=Property.TYPES.SELECT,
            is_product_type=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_type_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=product_type_property,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=product_type_value,
            language="en",
            value=f"Rule {product.id}",
        )
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=product_type_property,
            value_select=product_type_value,
        )
        return ProductPropertiesRule.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=product_type_value,
            sales_channel=sales_channel,
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

    def test_field_without_applicability_is_included_when_channel_validation_is_disabled(self):
        self.sales_channel.product_data_validation_by_channel = False
        self.sales_channel.save(update_fields=["product_data_validation_by_channel"])
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
            code="title",
            type="TEXT",
            local_instance=None,
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_TITLE,
        )
        baker.make(
            MiraklProductTypeItem,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type=product_type,
            remote_property=remote_property,
            required=True,
        )
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            language="en",
            sales_channel=None,
            name="English Name",
        )

        builder = MiraklProductPayloadBuilder(
            remote_product=remote_product,
            sales_channel_view=self.view,
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["title"], "English Name")

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

    def test_required_unit_without_default_value_raises_missing_value_error_not_mapping_error(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, _ = self._build_builder(
            remote_code="package_length_unit",
            local_property=local_property,
            required=True,
        )
        remote_property.local_instance = None
        remote_property.representation_type = remote_property.REPRESENTATION_UNIT
        remote_property.default_value = ""
        remote_property.save(update_fields=["local_instance", "representation_type", "default_value"])

        with self.assertRaisesMessage(
            PreFlightCheckError,
            "Mirakl preflight errors:\n- Mirakl required field 'package_length_unit' is missing for product SKU-1.",
        ):
            builder.build()

    def test_resolve_quantity_uses_starting_stock_when_remote_sku_missing(self):
        self.sales_channel.starting_stock = 7
        self.sales_channel.save(update_fields=["starting_stock"])
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, _, _ = self._build_builder(
            remote_code="collection",
            local_property=local_property,
            required=False,
            action=SalesChannelFeedItem.ACTION_UPDATE,
        )
        builder.remote_product.remote_sku = ""

        self.assertEqual(
            builder._resolve_quantity(product_context={"remote_product": builder.remote_product}),
            "7",
        )

    def test_resolve_quantity_uses_of21_when_remote_sku_exists(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, _, _ = self._build_builder(
            remote_code="collection",
            local_property=local_property,
            required=False,
            action=SalesChannelFeedItem.ACTION_CREATE,
        )
        builder.remote_product.remote_sku = "MKP-REMOTE-1"

        with patch.object(
            builder,
            "_mirakl_get",
            return_value={"offers": [{"active": True, "quantity": 9}], "total_count": 1},
        ) as mirakl_get_mock:
            self.assertEqual(
                builder._resolve_quantity(product_context={"remote_product": builder.remote_product}),
                "9",
            )

        mirakl_get_mock.assert_called_once_with(
            path="/api/offers",
            params={"product_id": "MKP-REMOTE-1", "shop_id": self.sales_channel.shop_id},
        )

    def test_resolve_quantity_skips_of21_for_delete_rows(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, _, _ = self._build_builder(
            remote_code="collection",
            local_property=local_property,
            required=False,
            action=SalesChannelFeedItem.ACTION_DELETE,
        )
        builder.remote_product.remote_sku = "MKP-REMOTE-1"

        with patch.object(builder, "_mirakl_get") as mirakl_get_mock:
            self.assertEqual(
                builder._resolve_quantity(product_context={"remote_product": builder.remote_product}),
                "",
            )

        mirakl_get_mock.assert_not_called()

    def test_resolve_quantity_raises_when_of21_returns_no_offer_for_existing_remote_sku(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, _, _ = self._build_builder(
            remote_code="collection",
            local_property=local_property,
            required=False,
            action=SalesChannelFeedItem.ACTION_CREATE,
        )
        builder.remote_product.remote_sku = "MKP-REMOTE-1"

        with patch.object(builder, "_mirakl_get", return_value={"offers": [], "total_count": 0}):
            with self.assertRaisesMessage(
                PreFlightCheckError,
                "Could not set quantity for product SKU-1: OF21 returned no usable offer for remote_sku 'MKP-REMOTE-1'.",
            ):
                builder._resolve_quantity(product_context={"remote_product": builder.remote_product})

    def test_resolve_quantity_prefers_first_active_offer_from_of21(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, _, _ = self._build_builder(
            remote_code="collection",
            local_property=local_property,
            required=False,
            action=SalesChannelFeedItem.ACTION_CREATE,
        )
        builder.remote_product.remote_sku = "MKP-REMOTE-1"

        with patch.object(
            builder,
            "_mirakl_get",
            return_value={
                "offers": [
                    {"active": False, "quantity": 3},
                    {"active": True, "quantity": 12},
                    {"active": True, "quantity": 18},
                ],
                "total_count": 3,
            },
        ):
            self.assertEqual(
                builder._resolve_quantity(product_context={"remote_product": builder.remote_product}),
                "12",
            )

    def test_create_factory_initialize_remote_product_does_not_seed_remote_sku(self):
        product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
            sku="SKU-1",
        )
        factory = MiraklProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product,
            view=self.view,
        )

        factory.initialize_remote_product()

        self.assertIsNone(factory.remote_instance.remote_sku)

    def test_create_factory_initialize_remote_product_switches_to_sync_when_remote_sku_exists(self):
        product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
            sku="SKU-1",
        )
        baker.make(
            MiraklProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_sku="MKP-REMOTE-1",
            remote_id="",
        )
        factory = MiraklProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product,
            view=self.view,
        )

        with self.assertRaisesMessage(
            SwitchedToSyncException,
            "RemoteProduct already exists with remote_sku: MKP-REMOTE-1. Switching to sync mode...",
        ):
            factory.initialize_remote_product()

    def test_create_action_uses_update_marker_in_offer_row(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, _, _ = self._build_builder(
            remote_code="collection",
            local_property=local_property,
            required=False,
            action=SalesChannelFeedItem.ACTION_CREATE,
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["update-delete"], "UPDATE")

    def test_delete_action_uses_delete_marker_in_offer_row(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, _, _ = self._build_builder(
            remote_code="collection",
            local_property=local_property,
            required=False,
            action=SalesChannelFeedItem.ACTION_DELETE,
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["update-delete"], "DELETE")

    def test_configurable_build_creates_variation_mirror_without_remote_sku(self):
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
            remote_sku=None,
        )
        parent_rule = self._assign_product_rule(
            product=parent_product,
            sales_channel=self.sales_channel,
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
            MiraklProductType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent_rule,
            remote_id="parent-cat",
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
        baker.make(
            MiraklPropertyApplicability,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            property=title_property,
            view=self.view,
        )
        baker.make(
            MiraklProductTypeItem,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type=product_type,
            remote_property=title_property,
            required=False,
        )
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=parent_product,
            language=self.multi_tenant_company.language,
            sales_channel=None,
            name="Parent Name",
        )

        _, rows = MiraklProductPayloadBuilder(
            remote_product=remote_product,
            sales_channel_view=self.view,
            action=SalesChannelFeedItem.ACTION_CREATE,
        ).build()

        variation_remote = MiraklProduct.objects.get(
            sales_channel=self.sales_channel,
            local_instance=child_product,
            remote_parent_product=remote_product,
        )
        self.assertEqual(len(rows), 1)
        self.assertTrue(variation_remote.is_variation)
        self.assertIsNone(variation_remote.remote_sku)

    def test_configurable_create_quantity_uses_variation_remote_sku_not_parent_remote_sku(self):
        self.sales_channel.starting_stock = 7
        self.sales_channel.save(update_fields=["starting_stock"])
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
            remote_sku="PARENT-REMOTE",
        )
        variation_remote = baker.make(
            MiraklProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=child_product,
            remote_parent_product=remote_product,
            is_variation=True,
            remote_sku="",
        )
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, _, _ = self._build_builder(
            remote_code="collection",
            local_property=local_property,
            required=False,
            action=SalesChannelFeedItem.ACTION_CREATE,
        )
        builder.remote_product = remote_product
        builder.local_product = parent_product

        self.assertEqual(
            builder._resolve_quantity(product_context={"remote_product": variation_remote}),
            "7",
        )

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
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=local_property,
            language="en",
            name="Colour",
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
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=local_select_value,
            language="en",
            value="Purple",
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
            "Missing Mirakl mappings:\n- Map the OneSila select value 'Purple' for Mirakl field 'colour' (local 'Colour') before pushing.",
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

    def test_logistic_class_offer_field_uses_mapped_remote_code_in_payload(self):
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
        logistic_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        logistic_local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=logistic_property,
        )
        baker.make(
            ProductProperty,
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=logistic_property,
            value_select=logistic_local_value,
        )
        remote_logistic_property = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="logistic_class",
            type=Property.TYPES.SELECT,
            local_instance=logistic_property,
            representation_type=MiraklProperty.REPRESENTATION_LOGISTIC_CLASS,
        )
        baker.make(
            MiraklPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=remote_logistic_property,
            local_instance=logistic_local_value,
            code="L",
            value="Large",
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["logistic-class"], "L")

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

    def test_required_swatch_uses_color_image_media(self):
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

        with patch.object(Media, "image_web_url", new=property(lambda self: "https://cdn.example.com/color.jpg")):
            _, rows = builder.build()

        self.assertEqual(rows[0]["swatch"], "https://cdn.example.com/color.jpg")

    @patch("media.models.Media.get_real_document_file", return_value="https://cdn.example.com/declaration.pdf")
    def test_document_representation_uses_mapped_local_document_type(self, _document_url_mock):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, product = self._build_builder(
            remote_code="pdf_declaration_of_identity",
            local_property=local_property,
            required=False,
        )
        remote_property.local_instance = None
        remote_property.representation_type = remote_property.REPRESENTATION_DOCUMENT
        remote_property.save(update_fields=["local_instance", "representation_type"])
        local_document_type = baker.make(
            DocumentType,
            multi_tenant_company=self.multi_tenant_company,
            name="Declaration of Identity",
        )
        baker.make(
            MiraklDocumentType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="pdf_declaration_of_identity",
            name="Declaration of Identity",
            local_instance=local_document_type,
        )
        media = baker.make(
            Media,
            multi_tenant_company=self.multi_tenant_company,
            type=Media.FILE,
            document_type=local_document_type,
        )
        baker.make(
            MediaProductThrough,
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            media=media,
            sales_channel=None,
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["pdf_declaration_of_identity"], "https://cdn.example.com/declaration.pdf")

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

    def test_configurable_variations_reuse_parent_content_and_prefer_variation_images(self):
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
        child_media = baker.make(
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
        baker.make(
            MediaProductThrough,
            multi_tenant_company=self.multi_tenant_company,
            product=child_product,
            media=child_media,
            is_main_image=True,
            sales_channel=None,
        )

        def _image_url(media_instance):
            if media_instance.id == child_media.id:
                return "https://cdn.example.com/child.jpg"
            if media_instance.id == media.id:
                return "https://cdn.example.com/parent.jpg"
            return ""

        with patch.object(Media, "image_web_url", new=property(_image_url)):
            _, rows = MiraklProductPayloadBuilder(
                remote_product=remote_product,
                sales_channel_view=self.view,
            ).build()

        self.assertEqual(rows[0]["title_field"], "Parent Name")
        self.assertEqual(rows[0]["main_image"], "https://cdn.example.com/child.jpg")

    def test_configurable_variations_fallback_to_parent_images_when_variation_has_none(self):
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

        with patch.object(Media, "image_web_url", new=property(lambda self: "https://cdn.example.com/parent.jpg")):
            _, rows = MiraklProductPayloadBuilder(
                remote_product=remote_product,
                sales_channel_view=self.view,
            ).build()

        self.assertEqual(rows[0]["title_field"], "Parent Name")
        self.assertEqual(rows[0]["main_image"], "https://cdn.example.com/parent.jpg")

    def test_configurable_create_requires_parent_mapping_even_when_child_is_mapped(self):
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
        baker.make(
            MiraklPropertyApplicability,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            property=title_property,
            view=self.view,
        )
        baker.make(
            MiraklProductTypeItem,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type=product_type,
            remote_property=title_property,
            required=False,
        )
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=parent_product,
            language=self.multi_tenant_company.language,
            sales_channel=None,
            name="Parent Name",
        )

        with self.assertRaisesMessage(
            MissingMappingError,
            "Map configurable parent product PARENT-1 to a Mirakl category or product type before pushing.",
        ):
            MiraklProductPayloadBuilder(
                remote_product=remote_product,
                sales_channel_view=self.view,
                action=SalesChannelFeedItem.ACTION_CREATE,
            ).build()

    def test_configurable_create_factory_preflight_requires_parent_mapping_even_when_child_is_mapped(self):
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
        category = baker.make(
            MiraklCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="cat-1",
            name="Category 1",
            is_leaf=True,
        )
        baker.make(
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

        factory = MiraklProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=parent_product,
            view=self.view,
        )

        with self.assertRaisesMessage(
            MissingMappingError,
            "Map configurable parent product PARENT-1 to a Mirakl category or product type before pushing.",
        ):
            factory.preflight_process()

    @override_settings(TESTING=False)
    def test_configurable_create_factory_preflight_requires_template_before_pushing(self):
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
        parent_rule = self._assign_product_rule(
            product=parent_product,
            sales_channel=self.sales_channel,
        )
        child_rule = self._assign_product_rule(
            product=child_product,
            sales_channel=self.sales_channel,
        )
        parent_category = baker.make(
            MiraklCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="parent-cat",
            name="Parent Category",
            is_leaf=True,
        )
        child_category = baker.make(
            MiraklCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="child-cat",
            name="Child Category",
            is_leaf=True,
        )
        baker.make(
            MiraklProductType,
            category=parent_category,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent_rule,
            remote_id="parent-cat",
            template=None,
        )
        baker.make(
            MiraklProductType,
            category=child_category,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=child_rule,
            remote_id="child-cat",
            template=None,
        )
        baker.make(
            MiraklProductCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=child_product,
            remote_id="child-cat",
        )

        factory = MiraklProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=parent_product,
            view=self.view,
        )

        with self.assertRaisesMessage(
            PreFlightCheckError,
            "Upload a CSV template for Mirakl product type 'parent-cat' before pushing configurable parent product PARENT-1.",
        ):
            factory.preflight_process()

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

    def test_parent_product_id_code_prefers_configurable_sku_in_fallback_detection(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, _ = self._build_builder(
            remote_code="parent_product_id",
            local_property=local_property,
            required=True,
        )
        remote_property.local_instance = None
        remote_property.representation_type = remote_property.REPRESENTATION_PROPERTY
        remote_property.save()

        _, rows = builder.build()

        self.assertEqual(rows[0]["parent_product_id"], "SKU-1")

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

    def test_product_title_representation_uses_remote_language_mapping(self):
        self.multi_tenant_company.language = "en"
        self.multi_tenant_company.save(update_fields=["language"])
        MiraklRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance="en",
            remote_code="en",
            label="English",
            is_default=True,
        )
        MiraklRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance="fr",
            remote_code="fr",
            label="French",
            is_default=False,
        )
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, product = self._build_builder(
            remote_code="product_title",
            local_property=local_property,
            required=False,
        )
        remote_property.local_instance = None
        remote_property.representation_type = remote_property.REPRESENTATION_PRODUCT_TITLE
        remote_property.save()
        product_type = MiraklProductType.objects.get(sales_channel=self.sales_channel, remote_id="cat-1")
        remote_property_fr = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="product_title_fr",
            local_instance=None,
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_TITLE,
            language="fr",
        )
        baker.make(
            MiraklPropertyApplicability,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            property=remote_property_fr,
            view=self.view,
        )
        baker.make(
            MiraklProductTypeItem,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type=product_type,
            remote_property=remote_property_fr,
            required=False,
        )
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            language="en",
            sales_channel=None,
            name="English Name",
        )
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            language="fr",
            sales_channel=None,
            name="Nom Francais",
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["product_title"], "English Name")
        self.assertEqual(rows[0]["product_title_fr"], "Nom Francais")

    def test_product_title_max_length_validation_blocks_long_name(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, product = self._build_builder(
            remote_code="product_title",
            local_property=local_property,
            required=True,
        )
        remote_property.local_instance = None
        remote_property.representation_type = remote_property.REPRESENTATION_PRODUCT_TITLE
        remote_property.validations = 'MAX_LENGTH|70,FORBIDDEN_WORDS|"pre-order,restricted"'
        remote_property.save()
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            language="en",
            sales_channel=None,
            name="A" * 71,
        )

        with self.assertRaisesMessage(
            PreFlightCheckError,
            "Mirakl preflight errors:\n- Mirakl field 'product_title' is longer than max length 70 for product SKU-1.",
        ):
            builder.build()

    def test_product_title_min_length_validation_blocks_short_name(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, product = self._build_builder(
            remote_code="product_title",
            local_property=local_property,
            required=True,
        )
        remote_property.local_instance = None
        remote_property.representation_type = remote_property.REPRESENTATION_PRODUCT_TITLE
        remote_property.validations = "MIN_LENGTH|5"
        remote_property.save()
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            language="en",
            sales_channel=None,
            name="Hat",
        )

        with self.assertRaisesMessage(
            PreFlightCheckError,
            "Mirakl preflight errors:\n- Mirakl field 'product_title' is shorter than min length 5 for product SKU-1.",
        ):
            builder.build()

    def test_product_title_forbidden_words_validation_blocks_name(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, product = self._build_builder(
            remote_code="product_title",
            local_property=local_property,
            required=True,
        )
        remote_property.local_instance = None
        remote_property.representation_type = remote_property.REPRESENTATION_PRODUCT_TITLE
        remote_property.validations = 'FORBIDDEN_WORDS|"pre-order,restricted"'
        remote_property.save()
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            language="en",
            sales_channel=None,
            name="Pre-order cotton shirt",
        )

        with self.assertRaisesMessage(
            PreFlightCheckError,
            "Mirakl preflight errors:\n- Mirakl field 'product_title' contains forbidden word 'pre-order' for product SKU-1.",
        ):
            builder.build()

    def test_translated_text_property_uses_remote_language_mapping(self):
        self.multi_tenant_company.language = "en"
        self.multi_tenant_company.save(update_fields=["language"])
        MiraklRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance="fr",
            remote_code="fr",
            label="French",
            is_default=False,
        )
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, product = self._build_builder(
            remote_code="care_label_fr",
            local_property=local_property,
            required=False,
        )
        remote_property.representation_type = remote_property.REPRESENTATION_PROPERTY
        remote_property.language = "fr"
        remote_property.save()
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=local_property,
        )
        ProductPropertyTextTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_property=product_property,
            language="en",
            value_text="English care",
        )
        ProductPropertyTextTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_property=product_property,
            language="fr",
            value_text="Conseils FR",
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["care_label_fr"], "Conseils FR")

    def test_remote_language_falls_back_to_company_language_when_unmapped(self):
        self.multi_tenant_company.language = "en"
        self.multi_tenant_company.save(update_fields=["language"])
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, product = self._build_builder(
            remote_code="product_title_fr",
            local_property=local_property,
            required=False,
        )
        remote_property.local_instance = None
        remote_property.representation_type = remote_property.REPRESENTATION_PRODUCT_TITLE
        remote_property.language = "fr"
        remote_property.save()
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            language="en",
            sales_channel=None,
            name="English Name",
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["product_title_fr"], "English Name")

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

    def test_product_reference_validation_is_collected_as_preflight_error(self):
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

        with self.assertRaisesMessage(
            PreFlightCheckError,
            "Mirakl preflight errors:\n- Mirakl field 'ean' is not a valid product reference for product SKU-1.",
        ):
            builder.build()

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

    def test_raw_validation_string_parses_known_validators_and_ignores_script(self):
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
        remote_property.validations = (
            'MAX_LENGTH|10,MIN_LENGTH|3,SCRIPT|"let patternArg = /foo,bar/;"|false,'
            'FORBIDDEN_WORDS|"scarface,mob"'
        )
        remote_property.save()

        self.assertEqual(
            builder._apply_remote_validations(
                remote_property=remote_property,
                value="Lamp",
                product_context={"sku": "SKU-1"},
            ),
            "Lamp",
        )

        with self.assertRaisesMessage(
            MiraklPayloadValidationError,
            "Mirakl field 'product_title' is longer than max length 10 for product SKU-1.",
        ):
            builder._apply_remote_validations(
                remote_property=remote_property,
                value="Elegant table lamp",
                product_context={"sku": "SKU-1"},
            )

        with self.assertRaisesMessage(
            MiraklPayloadValidationError,
            "Mirakl field 'product_title' contains forbidden word 'scarface' for product SKU-1.",
        ):
            builder._apply_remote_validations(
                remote_property=remote_property,
                value="Scarface",
                product_context={"sku": "SKU-1"},
            )

        self.assertEqual(
            builder._apply_remote_validations(
                remote_property=remote_property,
                value="Elegant",
                product_context={"sku": "SKU-1"},
            ),
            "Elegant",
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

    def test_details_and_care_resolves_from_property_value(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        builder, remote_property, product = self._build_builder(
            remote_code="details_and_care",
            local_property=local_property,
            required=True,
        )
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=local_property,
        )
        ProductPropertyTextTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_property=product_property,
            language=self.multi_tenant_company.language,
            value_text="Machine wash cold",
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["details_and_care"], "Machine wash cold")

    def test_description_field_mapped_to_select_uses_select_label_without_mirakl_option_mapping(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        builder, remote_property, product = self._build_builder(
            remote_code="details_and_care",
            local_property=local_property,
            required=True,
            remote_type=Property.TYPES.SELECT,
        )
        remote_property.original_type = Property.TYPES.DESCRIPTION
        remote_property.type = Property.TYPES.SELECT
        remote_property.save(update_fields=["original_type", "type"])

        select_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=local_property,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=select_value,
            language=self.multi_tenant_company.language,
            value="Machine wash cold",
        )
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=local_property,
            value_select=select_value,
        )

        _, rows = builder.build()

        self.assertEqual(rows[0]["details_and_care"], "Machine wash cold")

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
