from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker

from sales_channels.integrations.mirakl.factories.imports.schema_imports import (
    MiraklSchemaImportProcessor,
)
from sales_channels.integrations.mirakl.factories.sales_channels.full_schema import (
    MiraklFullSchemaSyncFactory,
)
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklDocumentType,
    MiraklInternalProperty,
    MiraklInternalPropertyOption,
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

    def _payloads_by_path(self):
        return {
            "/api/additional_fields": {
                "additional_fields": [
                    {
                        "code": "condition",
                        "label": "Condition",
                        "description": "Item condition",
                        "entity": "OFFER",
                        "type": "LIST",
                        "required": True,
                        "editable": True,
                        "accepted_values": "NEW,USED",
                    },
                    {
                        "code": "leadtime_to_ship",
                        "label": "Lead Time",
                        "description": "Shipping lead time",
                        "entity": "OFFER",
                        "type": "INTEGER",
                        "required": False,
                        "editable": True,
                    },
                ],
            },
            "/api/documents": {
                "documents": [
                    {
                        "code": "MANUAL",
                        "label": "Manual",
                        "description": "User manual",
                        "entity": "SHOP",
                        "mime_types": "application/pdf",
                    }
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
                        "code": "color",
                        "label": "Color",
                        "description": "Color attribute",
                        "hierarchy_code": "CHILD",
                        "required": True,
                        "variant": True,
                        "requirement_level": "REQUIRED",
                        "type": "LIST",
                        "values_list": "COLOR_LIST",
                        "channels": {"code": "WEB"},
                        "roles": [{"type": "PRODUCT", "parameters": [{"name": "scope", "value": "all"}]}],
                        "validations": '{"max": 10}',
                        "transformations": "[]",
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
                    }
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

        condition_property = MiraklInternalProperty.objects.get(
            sales_channel=self.sales_channel,
            code="condition",
        )
        leadtime_property = MiraklInternalProperty.objects.get(
            sales_channel=self.sales_channel,
            code="leadtime_to_ship",
        )
        self.assertTrue(condition_property.is_condition)
        self.assertFalse(leadtime_property.is_condition)
        self.assertEqual(
            MiraklInternalPropertyOption.objects.filter(internal_property=condition_property).count(),
            2,
        )

        parent = MiraklCategory.objects.get(sales_channel=self.sales_channel, remote_id="PARENT")
        child = MiraklCategory.objects.get(sales_channel=self.sales_channel, remote_id="CHILD")
        self.assertIsNone(parent.parent)
        self.assertFalse(parent.is_leaf)
        self.assertEqual(child.parent_id, parent.id)
        self.assertTrue(child.is_leaf)

        color_property = MiraklProperty.objects.get(sales_channel=self.sales_channel, code="color")
        self.assertEqual(color_property.value_list_code, "COLOR_LIST")
        self.assertEqual(color_property.value_list_label, "Colors")
        self.assertEqual(
            MiraklProductTypeItem.objects.filter(category=child, property=color_property).count(),
            1,
        )
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

        document_type = MiraklDocumentType.objects.get(
            sales_channel=self.sales_channel,
            remote_id="MANUAL",
        )
        self.assertEqual(document_type.name, "Manual")

        self.import_process.refresh_from_db()
        self.assertEqual(self.import_process.summary_data["internal_properties"], 2)
        self.assertEqual(summary["properties"], 2)


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
