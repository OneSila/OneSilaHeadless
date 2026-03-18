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
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertyApplicability,
    MiraklPropertySelectValue,
    MiraklSalesChannel,
    MiraklSalesChannelImport,
    MiraklSalesChannelView,
)


class MiraklFullSchemaSyncFactoryTests(TestCase):
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
        self.assertEqual(color_property.value_list_code, "COLOR_LIST")
        self.assertEqual(color_property.value_list_label, "Colors")
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
        self.assertEqual(package_length_property.name, "Package Length (cm)")
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
        self.assertEqual(made_to_order_property.default_value, "Yes")
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
        self.assertEqual(condition_property.value_list_code, "offer_states")
        self.assertEqual(condition_property.value_list_label, "Offer states")
        self.assertEqual(
            MiraklPropertySelectValue.objects.filter(remote_property=condition_property).count(),
            2,
        )
        self.assertFalse(
            MiraklProductTypeItem.objects.filter(remote_property=condition_property).exists()
        )

        self.import_process.refresh_from_db()
        self.assertGreaterEqual(summary["properties"], 4)


class MiraklSchemaImportProcessorTests(TestCase):
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

        with patch(
            "sales_channels.integrations.mirakl.factories.imports.schema_imports.MiraklFullSchemaSyncFactory"
        ) as mock_factory:
            mock_factory.return_value.run.return_value = {}
            processor.run()

        mock_factory.assert_called_once_with(
            sales_channel=self.sales_channel,
            import_process=self.import_process,
        )
        mock_factory.return_value.run.assert_called_once_with()

        self.import_process.refresh_from_db()
        self.assertEqual(self.import_process.status, MiraklSalesChannelImport.STATUS_SUCCESS)
        self.assertEqual(self.import_process.percentage, 100)

        self.sales_channel.refresh_from_db()
        self.assertTrue(self.sales_channel.active)
        self.assertFalse(self.sales_channel.is_importing)
