from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker
from properties.models import Property

from sales_channels.integrations.mirakl.factories.imports.schema_imports import (
    MiraklSchemaImportProcessor,
)
from sales_channels.integrations.mirakl.factories.sales_channels.full_schema import (
    MiraklFullSchemaSyncFactory,
)
from sales_channels.integrations.mirakl.factories.sync.public_definitions import (
    MiraklPublicDefinitionSyncFactory,
)
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklDocumentType,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertyApplicability,
    MiraklPropertySelectValue,
    MiraklPublicDefinition,
    MiraklSalesChannel,
    MiraklSalesChannelImport,
    MiraklSalesChannelView,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklFullSchemaSyncFactoryTests(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )
        self.view = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="WEB",
            name="Web",
        )
        self.import_process = baker.make(
            MiraklSalesChannelImport,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelImport.TYPE_SCHEMA,
        )

    def test_map_remote_type_handles_mirakl_specific_type_names(self):
        factory = MiraklFullSchemaSyncFactory(
            sales_channel=self.sales_channel,
            import_process=self.import_process,
        )

        expected_types = {
            "DATE": Property.TYPES.DATE,
            "DECIMAL": Property.TYPES.FLOAT,
            "LIST": Property.TYPES.SELECT,
            "LIST_MULTIPLE_VALUES": Property.TYPES.MULTISELECT,
            "LONG_TEXT": Property.TYPES.DESCRIPTION,
            "MEDIA": Property.TYPES.TEXT,
            "TEXT": Property.TYPES.TEXT,
            "NUMERIC": Property.TYPES.FLOAT,
            "TEXTAREA": Property.TYPES.DESCRIPTION,
            "REGEX": Property.TYPES.TEXT,
            "LINK": Property.TYPES.TEXT,
        }

        for remote_type, expected_property_type in expected_types.items():
            with self.subTest(remote_type=remote_type):
                self.assertEqual(
                    factory._map_remote_type(remote_type=remote_type),
                    expected_property_type,
                )

    def test_detect_representation_type_prefers_configurable_sku_for_configurable_id_codes(self):
        factory = MiraklFullSchemaSyncFactory(
            sales_channel=self.sales_channel,
            import_process=self.import_process,
        )

        for code in ["parent_product_id", "variant_group_code", "configurable_id"]:
            with self.subTest(code=code):
                self.assertEqual(
                    factory._detect_representation_type(
                        item={
                            "code": code,
                            "label": code,
                            "type": "TEXT",
                            "type_parameters": [],
                        },
                        values_list_code="",
                        inline_values=[],
                    ),
                    MiraklProperty.REPRESENTATION_PRODUCT_CONFIGURABLE_SKU,
                )

    def test_detect_representation_type_keeps_details_and_care_as_property(self):
        factory = MiraklFullSchemaSyncFactory(
            sales_channel=self.sales_channel,
            import_process=self.import_process,
        )

        self.assertEqual(
            factory._detect_representation_type(
                item={
                    "code": "details_and_care",
                    "label": "Details and Care",
                    "type": "TEXT",
                    "type_parameters": [],
                },
                values_list_code="",
                inline_values=[],
                ),
                MiraklProperty.REPRESENTATION_PROPERTY,
            )

    def test_detect_representation_type_does_not_treat_vox_mode_as_vat_rate(self):
        factory = MiraklFullSchemaSyncFactory(
            sales_channel=self.sales_channel,
            import_process=self.import_process,
        )

        self.assertEqual(
            factory._detect_representation_type(
                item={
                    "code": "Voice_activation_VOX_mode",
                    "label": "Voice activation VOX mode",
                    "type": "TEXT",
                    "type_parameters": [],
                },
                values_list_code="",
                inline_values=[],
            ),
            MiraklProperty.REPRESENTATION_PROPERTY,
        )

    def test_detect_representation_type_keeps_video_named_property_as_property(self):
        factory = MiraklFullSchemaSyncFactory(
            sales_channel=self.sales_channel,
            import_process=self.import_process,
        )

        self.assertEqual(
            factory._detect_representation_type(
                item={
                    "code": "Style_VideoPlayersRecorders",
                    "label": "Style Video Players Recorders",
                    "type": "TEXT",
                    "type_parameters": [],
                },
                values_list_code="",
                inline_values=[],
            ),
            MiraklProperty.REPRESENTATION_PROPERTY,
        )

    def test_detect_representation_type_uses_roles_mapping(self):
        factory = MiraklFullSchemaSyncFactory(
            sales_channel=self.sales_channel,
            import_process=self.import_process,
        )

        expected_types = {
            "CATEGORY": MiraklProperty.REPRESENTATION_PRODUCT_CATEGORY,
            "DESCRIPTION": MiraklProperty.REPRESENTATION_PRODUCT_DESCRIPTION,
            "MAIN_IMAGE": MiraklProperty.REPRESENTATION_THUMBNAIL_IMAGE,
            "SHOP_SKU": MiraklProperty.REPRESENTATION_PRODUCT_SKU,
            "TITLE": MiraklProperty.REPRESENTATION_PRODUCT_TITLE,
            "UNIQUE_IDENTIFIER": MiraklProperty.REPRESENTATION_PRODUCT_EAN,
            "VARIANT_GROUP_CODE": MiraklProperty.REPRESENTATION_PRODUCT_CONFIGURABLE_SKU,
        }

        for role_type, expected_representation_type in expected_types.items():
            with self.subTest(role_type=role_type):
                self.assertEqual(
                    factory._detect_representation_type(
                        item={
                            "code": f"custom_{role_type.lower()}",
                            "label": f"Custom {role_type.title()}",
                            "type": "TEXT",
                            "type_parameters": [],
                            "roles": [{"type": role_type}],
                        },
                        values_list_code="",
                        inline_values=[],
                    ),
                    expected_representation_type,
                )

    def test_apply_public_definition_sets_language(self):
        factory = MiraklFullSchemaSyncFactory(
            sales_channel=self.sales_channel,
            import_process=self.import_process,
        )
        MiraklPublicDefinition.objects.create(
            hostname=self.sales_channel.hostname,
            property_code="product_title_fr",
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_TITLE,
            language="fr",
        )
        remote_property = MiraklProperty(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            code="product_title_fr",
            representation_type=MiraklProperty.REPRESENTATION_PROPERTY,
        )

        factory._apply_public_definition(remote_property=remote_property)

        self.assertEqual(remote_property.representation_type, MiraklProperty.REPRESENTATION_PRODUCT_TITLE)
        self.assertEqual(remote_property.language, "fr")
        self.assertTrue(remote_property.representation_type_decided)

    def test_public_definition_sync_persists_language(self):
        remote_property = baker.make(
            MiraklProperty,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            code="product_title_fr",
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_TITLE,
            representation_type_decided=False,
            language="fr",
        )

        synced = MiraklPublicDefinitionSyncFactory(sales_channel=self.sales_channel).run()

        self.assertEqual(synced, 1)
        remote_property.refresh_from_db()
        self.assertTrue(remote_property.representation_type_decided)
        public_definition = MiraklPublicDefinition.objects.get(
            hostname=self.sales_channel.hostname,
            property_code="product_title_fr",
        )
        self.assertEqual(public_definition.language, "fr")

    def test_public_definition_sync_creates_document_type_for_document_property(self):
        remote_property = baker.make(
            MiraklProperty,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            code="energy_label",
            name="Energy label",
            description="Energy label asset",
            representation_type=MiraklProperty.REPRESENTATION_DOCUMENT,
            representation_type_decided=False,
        )

        synced = MiraklPublicDefinitionSyncFactory(sales_channel=self.sales_channel).run()

        self.assertEqual(synced, 1)
        remote_property.refresh_from_db()
        self.assertTrue(remote_property.representation_type_decided)
        document_type = MiraklDocumentType.objects.get(
            sales_channel=self.sales_channel,
            remote_id="energy_label",
        )
        self.assertEqual(document_type.name, "Energy label")
        self.assertEqual(document_type.description, "Energy label asset")

    def _payloads_by_path(self):
        return {
            "/api/offers/states": {
                "offer_states": [
                    {
                        "active": True,
                        "code": "10",
                        "label": "Refurbished",
                    },
                    {
                        "active": True,
                        "code": "11",
                        "label": "New",
                    },
                ],
            },
            "/api/shipping/logistic_classes": {
                "logistic_classes": [
                    {
                        "code": "S",
                        "description": "Small",
                        "label": "Small",
                    },
                    {
                        "code": "L",
                        "description": "Large",
                        "label": "Large",
                    },
                ],
            },
            "/api/hierarchies": {
                "hierarchies": [
                    {"code": "PARENT", "label": "Parent", "level": 1, "parent_code": ""},
                    {"code": "CHILD", "label": "Child", "level": 2, "parent_code": "PARENT"},
                ],
            },
            "/api/products/attributes": {
                "attributes": [
                    {
                        "code": "fit_note",
                        "label": "Fit Note",
                        "hierarchy_code": "PARENT",
                        "required": False,
                        "variant": False,
                        "type": "TEXT",
                        "channels": [{"code": "WEB"}],
                    },
                    {
                        "code": "color",
                        "label": "Color",
                        "description": "Color attribute",
                        "description_translations": [{"locale": "en_GB", "value": "Color attribute"}],
                        "label_translations": [{"locale": "en_GB", "value": "Color"}],
                        "example": "Red",
                        "hierarchy_code": "CHILD",
                        "required": True,
                        "variant": True,
                        "requirement_level": "REQUIRED",
                        "type": "LIST",
                        "type_parameters": [
                            {"name": "LIST_CODE", "value": "COLOR_LIST"},
                            {"name": "format", "value": "text"},
                        ],
                        "values_list": "",
                        "channels": {"code": "WEB"},
                        "roles": [{"type": "PRODUCT", "parameters": [{"name": "scope", "value": "all"}]}],
                        "validations": '{"max": 10}',
                        "transformations": "[]",
                    },
                    {
                        "code": "fit_note",
                        "label": "Fit Note Child",
                        "description": "Child-specific fit note",
                        "hierarchy_code": "CHILD",
                        "required": True,
                        "variant": True,
                        "requirement_level": "REQUIRED",
                        "type": "TEXT",
                        "channels": [{"code": "WEB"}],
                    },
                    {
                        "code": "size_note",
                        "label": "Size Note",
                        "description": "Free text note",
                        "hierarchy_code": "CHILD",
                        "required": False,
                        "variant": False,
                        "type": "TEXT",
                        "values": [{"code": "SMALL", "label": "Small"}],
                        "channels": [{"code": "WEB"}],
                    },
                    {
                        "code": "height_7_uom",
                        "label": "Height Unit",
                        "hierarchy_code": "CHILD",
                        "required": True,
                        "variant": True,
                        "type": "LIST",
                        "values_list": "HEIGHT_UNITS",
                        "channels": [{"code": "WEB"}],
                    },
                    {
                        "code": "category2_child",
                        "label": "Category2 Child",
                        "hierarchy_code": "CHILD",
                        "required": True,
                        "variant": False,
                        "type": "LIST",
                        "type_parameters": [
                            {"name": "LIST_CODE", "value": "CATEGORY2_CHILD"},
                            {"name": "DEFAULT_VALUE", "value": "child_default"},
                        ],
                        "channels": [{"code": "WEB"}],
                    },
                    {
                        "code": "package_length",
                        "label": "Package Length",
                        "hierarchy_code": "CHILD",
                        "required": False,
                        "variant": False,
                        "type": "NUMERIC",
                        "type_parameters": [
                            {"name": "PRECISION", "value": "2"},
                            {"name": "UNIT", "value": "cm"},
                        ],
                        "channels": [{"code": "WEB"}],
                    },
                    {
                        "code": "pdf_declaration_of_identity",
                        "label": "Declaration of Identity",
                        "description": "Identity declaration PDF",
                        "hierarchy_code": "CHILD",
                        "required": True,
                        "variant": False,
                        "requirement_level": "REQUIRED",
                        "type": "MEDIA",
                        "type_parameters": [{"name": "TYPE", "value": "DOCUMENT"}],
                        "channels": [{"code": "WEB"}],
                    },
                    {
                        "code": "pdf_care_label",
                        "label": "Care Label",
                        "description": "Care label PDF",
                        "hierarchy_code": "",
                        "required": False,
                        "variant": False,
                        "requirement_level": "OPTIONAL",
                        "type": "MEDIA",
                        "type_parameters": [{"name": "TYPE", "value": "DOCUMENT"}],
                        "channels": [{"code": "WEB"}],
                    },
                    {
                        "code": "product_title",
                        "label": "Product Title",
                        "hierarchy_code": "",
                        "required": True,
                        "variant": False,
                        "type": "TEXT",
                        "channels": [{"code": "WEB"}],
                    },
                    {
                        "code": "made_to_order",
                        "label": "Made To Order",
                        "hierarchy_code": "",
                        "required": False,
                        "variant": False,
                        "type": "LIST",
                        "values_list": "YES_ONLY",
                        "channels": [{"code": "WEB"}],
                    },
                ],
            },
            "/api/values_lists": {
                "values_lists": [
                    {
                        "code": "COLOR_LIST",
                        "label": "Colors",
                        "values": [
                            {"code": "RED", "label": "Red"},
                            {"code": "BLU", "label": "Blue"},
                        ],
                    },
                    {
                        "code": "HEIGHT_UNITS",
                        "label": "Height Units",
                        "values": [
                            {"code": "CM", "label": "Centimetres"},
                        ],
                    },
                    {
                        "code": "YES_ONLY",
                        "label": "Yes Only",
                        "values": [
                            {"code": "yes", "label": "Yes"},
                        ],
                    },
                    {
                        "code": "CATEGORY2_CHILD",
                        "label": "Category2 Child",
                        "values": [
                            {"code": "child_default", "label": "Child Default"},
                            {"code": "other", "label": "Other"},
                        ],
                    },
                ],
            },
        }

    def test_run_imports_schema_records(self):
        self.sales_channel.product_data_validation_by_channel = True
        self.sales_channel.save(update_fields=["product_data_validation_by_channel"])
        payloads = self._payloads_by_path()

        def mirakl_get_side_effect(*, path, params=None, timeout=None):
            return payloads[path]

        factory = MiraklFullSchemaSyncFactory(
            sales_channel=self.sales_channel,
            import_process=self.import_process,
        )

        with patch.object(factory, "mirakl_get", side_effect=mirakl_get_side_effect):
            summary = factory.run()

        parent = MiraklCategory.objects.get(sales_channel=self.sales_channel, remote_id="PARENT")
        child = MiraklCategory.objects.get(sales_channel=self.sales_channel, remote_id="CHILD")
        self.assertIsNone(parent.parent)
        self.assertFalse(parent.is_leaf)
        self.assertEqual(child.parent_id, parent.id)
        self.assertTrue(child.is_leaf)

        color_property = MiraklProperty.objects.get(sales_channel=self.sales_channel, code="color")
        self.assertEqual(color_property.representation_type, MiraklProperty.REPRESENTATION_PROPERTY)
        self.assertEqual(color_property.example, "Red")
        self.assertFalse(color_property.is_common)
        self.assertFalse(color_property.allows_unmapped_values)
        self.assertEqual(color_property.description_translations, [{"locale": "en_GB", "value": "Color attribute"}])
        self.assertEqual(color_property.label_translations, [{"locale": "en_GB", "value": "Color"}])
        self.assertEqual(
            color_property.type_parameters,
            [
                {"name": "LIST_CODE", "value": "COLOR_LIST"},
                {"name": "format", "value": "text"},
            ],
        )
        child_product_type = MiraklProductType.objects.get(
            sales_channel=self.sales_channel,
            remote_id="CHILD",
        )
        parent_product_type = MiraklProductType.objects.get(
            sales_channel=self.sales_channel,
            remote_id="PARENT",
        )
        self.assertEqual(
            MiraklProductTypeItem.objects.filter(product_type=child_product_type, remote_property=color_property).count(),
            1,
        )
        color_item = MiraklProductTypeItem.objects.get(product_type=child_product_type, remote_property=color_property)
        self.assertEqual(color_item.hierarchy_code, "CHILD")
        self.assertEqual(color_item.requirement_level, "REQUIRED")
        self.assertTrue(color_item.required)
        self.assertTrue(color_item.variant)
        self.assertEqual(color_item.value_list_code, "COLOR_LIST")
        self.assertEqual(color_item.value_list_label, "Colors")
        self.assertEqual(
            MiraklPropertyApplicability.objects.filter(property=color_property, view=self.view).count(),
            1,
        )
        self.assertEqual(
            MiraklPropertySelectValue.objects.filter(remote_property=color_property).count(),
            2,
        )
        inline_property = MiraklProperty.objects.get(sales_channel=self.sales_channel, code="size_note")
        self.assertEqual(
            MiraklPropertySelectValue.objects.filter(remote_property=inline_property).count(),
            1,
        )
        unit_property = MiraklProperty.objects.get(sales_channel=self.sales_channel, code="height_7_uom")
        self.assertEqual(unit_property.representation_type, MiraklProperty.REPRESENTATION_UNIT)
        self.assertEqual(unit_property.default_value, "")
        self.assertFalse(unit_property.allows_unmapped_values)
        category2_child_property = MiraklProperty.objects.get(sales_channel=self.sales_channel, code="category2_child")
        self.assertEqual(category2_child_property.representation_type, MiraklProperty.REPRESENTATION_PROPERTY)
        self.assertEqual(category2_child_property.default_value, "child_default")
        package_length_property = MiraklProperty.objects.get(sales_channel=self.sales_channel, code="package_length")
        self.assertEqual(package_length_property.representation_type, MiraklProperty.REPRESENTATION_PROPERTY)
        self.assertEqual(package_length_property.name, "Package Length (cm)")
        declaration_property = MiraklProperty.objects.get(
            sales_channel=self.sales_channel,
            code="pdf_declaration_of_identity",
        )
        self.assertEqual(declaration_property.representation_type, MiraklProperty.REPRESENTATION_DOCUMENT)
        declaration_document_type = MiraklDocumentType.objects.get(
            sales_channel=self.sales_channel,
            remote_id="pdf_declaration_of_identity",
        )
        self.assertEqual(declaration_document_type.name, "Declaration of Identity")
        self.assertEqual(declaration_document_type.description, "Identity declaration PDF")
        self.assertEqual(declaration_document_type.required_categories, ["CHILD"])
        self.assertEqual(declaration_document_type.optional_categories, [])
        care_label_document_type = MiraklDocumentType.objects.get(
            sales_channel=self.sales_channel,
            remote_id="pdf_care_label",
        )
        self.assertEqual(care_label_document_type.required_categories, [])
        self.assertEqual(care_label_document_type.optional_categories, ["CHILD", "PARENT"])
        title_property = MiraklProperty.objects.get(sales_channel=self.sales_channel, code="product_title")
        self.assertEqual(title_property.representation_type, MiraklProperty.REPRESENTATION_PRODUCT_TITLE)
        self.assertTrue(title_property.is_common)
        self.assertTrue(title_property.allows_unmapped_values)
        self.assertEqual(
            MiraklProductTypeItem.objects.filter(product_type=parent_product_type, remote_property=title_property).count(),
            1,
        )
        self.assertEqual(
            MiraklProductTypeItem.objects.filter(product_type=child_product_type, remote_property=title_property).count(),
            1,
        )

        made_to_order_property = MiraklProperty.objects.get(sales_channel=self.sales_channel, code="made_to_order")
        self.assertEqual(made_to_order_property.representation_type, MiraklProperty.REPRESENTATION_DEFAULT_VALUE)
        self.assertEqual(made_to_order_property.default_value, "yes")
        self.assertEqual(
            MiraklProductTypeItem.objects.filter(product_type=parent_product_type, remote_property=made_to_order_property).count(),
            1,
        )
        self.assertEqual(
            MiraklProductTypeItem.objects.filter(product_type=child_product_type, remote_property=made_to_order_property).count(),
            1,
        )

        fit_note_property = MiraklProperty.objects.get(sales_channel=self.sales_channel, code="fit_note")
        parent_fit_note_item = MiraklProductTypeItem.objects.get(
            product_type=parent_product_type,
            remote_property=fit_note_property,
        )
        child_fit_note_item = MiraklProductTypeItem.objects.get(
            product_type=child_product_type,
            remote_property=fit_note_property,
        )
        self.assertEqual(parent_fit_note_item.hierarchy_code, "PARENT")
        self.assertFalse(parent_fit_note_item.required)
        self.assertFalse(parent_fit_note_item.variant)
        self.assertEqual(child_fit_note_item.hierarchy_code, "CHILD")
        self.assertTrue(child_fit_note_item.required)
        self.assertTrue(child_fit_note_item.variant)

        condition_property = MiraklProperty.objects.get(sales_channel=self.sales_channel, code="offer_state")
        self.assertEqual(condition_property.representation_type, MiraklProperty.REPRESENTATION_CONDITION)
        self.assertEqual(condition_property.type, Property.TYPES.SELECT)
        self.assertFalse(condition_property.allows_unmapped_values)
        self.assertEqual(
            MiraklPropertySelectValue.objects.filter(remote_property=condition_property).count(),
            2,
        )
        self.assertFalse(
            MiraklProductTypeItem.objects.filter(remote_property=condition_property).exists()
        )

        logistic_class_property = MiraklProperty.objects.get(sales_channel=self.sales_channel, code="logistic_class")
        self.assertEqual(logistic_class_property.representation_type, MiraklProperty.REPRESENTATION_LOGISTIC_CLASS)
        self.assertEqual(logistic_class_property.type, Property.TYPES.SELECT)
        self.assertFalse(logistic_class_property.allows_unmapped_values)
        self.assertEqual(
            MiraklPropertySelectValue.objects.filter(remote_property=logistic_class_property).count(),
            2,
        )
        self.assertFalse(
            MiraklProductTypeItem.objects.filter(remote_property=logistic_class_property).exists()
        )

        self.import_process.refresh_from_db()
        self.assertGreaterEqual(summary["properties"], 4)

    def test_run_imports_select_values_for_all_item_level_value_lists_of_same_property(self):
        payloads = {
            "/api/offers/states": {"offer_states": []},
            "/api/shipping/logistic_classes": {"logistic_classes": []},
            "/api/hierarchies": {
                "hierarchies": [
                    {"code": "TYPE_A", "label": "Type A", "level": 1, "parent_code": ""},
                    {"code": "TYPE_B", "label": "Type B", "level": 1, "parent_code": ""},
                ],
            },
            "/api/products/attributes": {
                "attributes": [
                    {
                        "code": "core_property",
                        "label": "Core Property",
                        "hierarchy_code": "TYPE_A",
                        "required": False,
                        "variant": False,
                        "type": "LIST",
                        "type_parameters": [{"name": "LIST_CODE", "value": "LIST_A"}],
                        "channels": [{"code": "WEB"}],
                    },
                    {
                        "code": "core_property",
                        "label": "Core Property",
                        "hierarchy_code": "TYPE_B",
                        "required": False,
                        "variant": False,
                        "type": "LIST",
                        "type_parameters": [{"name": "LIST_CODE", "value": "LIST_B"}],
                        "channels": [{"code": "WEB"}],
                    },
                ],
            },
            "/api/values_lists": {
                "values_lists": [
                    {
                        "code": "LIST_A",
                        "label": "List A",
                        "values": [
                            {"code": "A1", "label": "Alpha One"},
                            {"code": "A2", "label": "Alpha Two"},
                        ],
                    },
                    {
                        "code": "LIST_B",
                        "label": "List B",
                        "values": [
                            {"code": "B1", "label": "Beta One"},
                            {"code": "B2", "label": "Beta Two"},
                        ],
                    },
                ],
            },
        }

        def mirakl_get_side_effect(*, path, params=None, timeout=None):
            return payloads[path]

        factory = MiraklFullSchemaSyncFactory(
            sales_channel=self.sales_channel,
            import_process=self.import_process,
        )

        with patch.object(factory, "mirakl_get", side_effect=mirakl_get_side_effect):
            factory.run()

        remote_property = MiraklProperty.objects.get(
            sales_channel=self.sales_channel,
            code="core_property",
        )
        type_a = MiraklProductType.objects.get(sales_channel=self.sales_channel, remote_id="TYPE_A")
        type_b = MiraklProductType.objects.get(sales_channel=self.sales_channel, remote_id="TYPE_B")
        self.assertEqual(
            MiraklProductTypeItem.objects.get(product_type=type_a, remote_property=remote_property).value_list_code,
            "LIST_A",
        )
        self.assertEqual(
            MiraklProductTypeItem.objects.get(product_type=type_b, remote_property=remote_property).value_list_code,
            "LIST_B",
        )
        self.assertCountEqual(
            list(
                MiraklPropertySelectValue.objects.filter(
                    remote_property=remote_property,
                ).values_list("code", flat=True)
            ),
            ["A1", "A2", "B1", "B2"],
        )

    def test_run_import_uses_roles_for_representation_type_detection(self):
        payloads = {
            "/api/offers/states": {
                "offer_states": [],
            },
            "/api/shipping/logistic_classes": {
                "logistic_classes": [],
            },
            "/api/hierarchies": {
                "hierarchies": [
                    {"code": "CHILD", "label": "Child", "level": 1, "parent_code": ""},
                ],
            },
            "/api/products/attributes": {
                "attributes": [
                    {
                        "code": "content_block",
                        "label": "Content Block",
                        "hierarchy_code": "CHILD",
                        "required": False,
                        "variant": False,
                        "type": "TEXT",
                        "channels": [{"code": "WEB"}],
                        "roles": [{"type": "DESCRIPTION"}],
                    },
                    {
                        "code": "hero_asset",
                        "label": "Hero Asset",
                        "hierarchy_code": "CHILD",
                        "required": False,
                        "variant": False,
                        "type": "MEDIA",
                        "type_parameters": [{"name": "TYPE", "value": "IMAGE"}],
                        "channels": [{"code": "WEB"}],
                        "roles": [{"type": "MAIN_IMAGE"}],
                    },
                    {
                        "code": "catalog_group",
                        "label": "Catalog Group",
                        "hierarchy_code": "CHILD",
                        "required": False,
                        "variant": True,
                        "type": "TEXT",
                        "channels": [{"code": "WEB"}],
                        "roles": [{"type": "VARIANT_GROUP_CODE"}],
                    },
                ],
            },
            "/api/values_lists": {
                "values_lists": [],
            },
        }

        def mirakl_get_side_effect(*, path, params=None, timeout=None):
            return payloads[path]

        factory = MiraklFullSchemaSyncFactory(
            sales_channel=self.sales_channel,
            import_process=self.import_process,
        )

        with patch.object(factory, "mirakl_get", side_effect=mirakl_get_side_effect):
            factory.run()

        self.assertEqual(
            MiraklProperty.objects.get(
                sales_channel=self.sales_channel,
                code="content_block",
            ).representation_type,
            MiraklProperty.REPRESENTATION_PRODUCT_DESCRIPTION,
        )
        self.assertEqual(
            MiraklProperty.objects.get(
                sales_channel=self.sales_channel,
                code="hero_asset",
            ).representation_type,
            MiraklProperty.REPRESENTATION_THUMBNAIL_IMAGE,
        )
        self.assertEqual(
            MiraklProperty.objects.get(
                sales_channel=self.sales_channel,
                code="catalog_group",
            ).representation_type,
            MiraklProperty.REPRESENTATION_PRODUCT_CONFIGURABLE_SKU,
        )

    def test_upsert_property_reopens_decided_default_value_when_attribute_now_has_multiple_values(self):
        factory = MiraklFullSchemaSyncFactory(
            sales_channel=self.sales_channel,
            import_process=self.import_process,
        )
        remote_property = baker.make(
            MiraklProperty,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            code="made_to_order",
            representation_type=MiraklProperty.REPRESENTATION_DEFAULT_VALUE,
            representation_type_decided=True,
            raw_data={"code": "made_to_order", "hierarchy_code": ""},
        )

        factory._upsert_property(
            item={
                "code": "made_to_order",
                "label": "Made To Order",
                "hierarchy_code": "",
                "required": False,
                "variant": False,
                "type": "LIST",
                "values": [
                    {"code": "yes", "label": "Yes"},
                    {"code": "no", "label": "No"},
                ],
                "channels": [{"code": "WEB"}],
            }
        )

        remote_property.refresh_from_db()
        self.assertEqual(remote_property.representation_type, MiraklProperty.REPRESENTATION_PROPERTY)
        self.assertFalse(remote_property.representation_type_decided)

    def test_upsert_property_auto_maps_brand_role_to_local_brand_property(self):
        factory = MiraklFullSchemaSyncFactory(
            sales_channel=self.sales_channel,
            import_process=self.import_process,
        )
        local_brand_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="brand",
        )

        remote_property = factory._upsert_property(
            item={
                "code": "product_brand",
                "label": "Brand",
                "hierarchy_code": "",
                "required": False,
                "variant": False,
                "type": "SELECT",
                "roles": [{"type": "BRAND"}],
                "channels": [{"code": "WEB"}],
            }
        )

        self.assertIsNotNone(remote_property)
        remote_property.refresh_from_db()
        self.assertEqual(remote_property.local_instance_id, local_brand_property.id)
        self.assertEqual(remote_property.representation_type, MiraklProperty.REPRESENTATION_PROPERTY)

    def test_upsert_property_brand_role_does_not_override_existing_local_mapping(self):
        factory = MiraklFullSchemaSyncFactory(
            sales_channel=self.sales_channel,
            import_process=self.import_process,
        )
        existing_local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            internal_name="manufacturer",
            type=Property.TYPES.TEXT,
        )
        Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="brand",
            defaults={"type": Property.TYPES.TEXT},
        )
        remote_property = baker.make(
            MiraklProperty,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            code="product_brand",
            local_instance=existing_local_property,
        )

        updated_property = factory._upsert_property(
            item={
                "code": "product_brand",
                "label": "Brand",
                "hierarchy_code": "",
                "required": False,
                "variant": False,
                "type": "TEXT",
                "roles": [{"type": "BRAND"}],
                "channels": [{"code": "WEB"}],
            }
        )

        self.assertIsNotNone(updated_property)
        remote_property.refresh_from_db()
        self.assertEqual(remote_property.local_instance_id, existing_local_property.id)

class MiraklSchemaImportProcessorTests(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
            active=True,
            is_importing=False,
        )
        self.import_process = baker.make(
            MiraklSalesChannelImport,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelImport.TYPE_SCHEMA,
        )

    def test_run_invokes_full_schema_factory(self):
        processor = MiraklSchemaImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )

        with (
            self.assertLogs(
                "sales_channels.integrations.mirakl.factories.imports.schema_imports",
                level="INFO",
            ) as captured,
            patch(
                "sales_channels.integrations.mirakl.factories.imports.schema_imports.MiraklSalesChannelViewPullFactory"
            ) as mock_view_pull_factory,
            patch(
                "sales_channels.integrations.mirakl.factories.imports.schema_imports.MiraklFullSchemaSyncFactory"
            ) as mock_factory,
        ):
            mock_view_pull_factory.return_value.run.return_value = None
            mock_factory.return_value.run.return_value = {}
            processor.run()

        mock_view_pull_factory.assert_called_once_with(sales_channel=self.sales_channel)
        mock_view_pull_factory.return_value.run.assert_called_once_with()
        mock_factory.assert_called_once_with(
            sales_channel=self.sales_channel,
            import_process=self.import_process,
        )
        mock_factory.return_value.run.assert_called_once_with()

        logs = "\n".join(captured.output)
        self.assertIn("Preparing Mirakl schema import", logs)
        self.assertIn("Mirakl schema import completed", logs)
        self.assertIn("Restored Mirakl schema import channel state", logs)

        self.import_process.refresh_from_db()
        self.assertEqual(self.import_process.status, MiraklSalesChannelImport.STATUS_SUCCESS)
        self.assertEqual(self.import_process.percentage, 100)

        self.sales_channel.refresh_from_db()
        self.assertTrue(self.sales_channel.active)
        self.assertFalse(self.sales_channel.is_importing)

    def test_run_logs_failure_and_restores_channel_state(self):
        processor = MiraklSchemaImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )

        with (
            self.assertLogs(
                "sales_channels.integrations.mirakl.factories.imports.schema_imports",
                level="INFO",
            ) as captured,
            patch(
                "sales_channels.integrations.mirakl.factories.imports.schema_imports.MiraklSalesChannelViewPullFactory"
            ) as mock_view_pull_factory,
            patch(
                "sales_channels.integrations.mirakl.factories.imports.schema_imports.MiraklFullSchemaSyncFactory"
            ) as mock_factory,
            self.assertRaises(RuntimeError),
        ):
            mock_view_pull_factory.return_value.run.return_value = None
            mock_factory.return_value.run.side_effect = RuntimeError("schema exploded")
            processor.run()

        mock_view_pull_factory.assert_called_once_with(sales_channel=self.sales_channel)
        mock_view_pull_factory.return_value.run.assert_called_once_with()

        logs = "\n".join(captured.output)
        self.assertIn("Preparing Mirakl schema import", logs)
        self.assertIn("Mirakl schema import failed", logs)
        self.assertIn("Restored Mirakl schema import channel state", logs)

        self.import_process.refresh_from_db()
        self.assertEqual(self.import_process.status, MiraklSalesChannelImport.STATUS_FAILED)

        self.sales_channel.refresh_from_db()
        self.assertTrue(self.sales_channel.active)
        self.assertFalse(self.sales_channel.is_importing)
