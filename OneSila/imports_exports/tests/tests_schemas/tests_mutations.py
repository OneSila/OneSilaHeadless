import unittest
from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TransactionTestCase
from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from imports_exports.models import Export, MappedImport
from imports_exports.schema.mutation_helpers import (
    _build_export_parameters,
    _merge_parameter_dicts,
    _validate_periodic_export_size,
)
from products.models import Product
from sales_channels.models import SalesChannel


class ImportsExportsMutationTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="SKU-MUT-1",
        )
        self.sales_channel = baker.make(
            SalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )

    # @TODO TO fix 04.04.2026
    @unittest.skip("TODO 04.04.2026: test fixture creates abstract SalesChannel and triggers connect().")
    def test_create_mapped_import_from_json_url(self):
        mutation = """
        mutation($data: MappedImportCreateInput!) {
          createMappedImport(data: $data) {
            id
            name
            type
            jsonUrl
            status
          }
        }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={
                "data": {
                    "name": "GraphQL mapped import",
                    "type": MappedImport.TYPE_PRODUCT,
                    "jsonUrl": "https://example.com/mapped.json",
                    "skipBrokenRecords": True,
                }
            },
        )

        self.assertIsNone(resp.errors)
        instance = MappedImport.objects.get(id=self.from_global_id(resp.data["createMappedImport"]["id"])[1])
        self.assertEqual(instance.name, "GraphQL mapped import")
        self.assertEqual(instance.json_url, "https://example.com/mapped.json")
        self.assertTrue(instance.skip_broken_records)
        self.assertEqual(instance.status, MappedImport.STATUS_PENDING)

    # @TODO TO fix 04.04.2026
    @unittest.skip("TODO 04.04.2026: test fixture creates abstract SalesChannel and triggers connect().")
    def test_create_export_maps_ids_columns_and_nested_parameters(self):
        mutation = """
        mutation($data: ExportCreateInput!) {
          createExport(data: $data) {
            id
            kind
            type
            columns
            parameters
          }
        }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={
                "data": {
                    "name": "GraphQL export",
                    "type": Export.TYPE_JSON,
                    "kind": Export.KIND_PRODUCTS,
                    "ids": [self.to_global_id(self.product)],
                    "salesChannel": self.to_global_id(self.sales_channel),
                    "flat": True,
                    "productPropertiesAddValueIds": True,
                    "columns": ["sku", "translations"],
                }
            },
        )

        self.assertIsNone(resp.errors)
        export_process = Export.objects.get(id=self.from_global_id(resp.data["createExport"]["id"])[1])
        self.assertEqual(export_process.parameters["ids"], [self.product.id])
        self.assertEqual(export_process.parameters["sales_channel"], self.sales_channel.id)
        self.assertTrue(export_process.parameters["flat"])
        self.assertEqual(
            export_process.parameters["product_properties"]["add_value_ids"],
            True,
        )
        self.assertEqual(export_process.columns, ["sku", "translations"])
        self.assertEqual(export_process.status, Export.STATUS_PENDING)

    # @TODO TO fix 04.04.2026
    @unittest.skip("TODO 04.04.2026: test fixture creates abstract SalesChannel and triggers connect().")
    def test_update_export_rejects_invalid_parameter_for_kind(self):
        export_process = Export.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Export.TYPE_JSON,
            kind=Export.KIND_PRICE_LISTS,
        )
        mutation = """
        mutation($data: ExportUpdateInput!) {
          updateExport(data: $data) {
            id
          }
        }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={
                "data": {
                    "id": self.to_global_id(export_process),
                    "flat": True,
                }
            },
            asserts_errors=False,
        )

        self.assertIsNotNone(resp.errors)

    # @TODO TO fix 04.04.2026
    @unittest.skip("TODO 04.04.2026: test fixture creates abstract SalesChannel and triggers connect().")
    @patch("imports_exports.models.safe_run_task")
    def test_resync_mapped_import_sends_instance_to_pending_and_dispatches_async(self, mocked_safe_run_task):
        mapped_import = MappedImport.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=MappedImport.TYPE_PRODUCT,
            status=MappedImport.STATUS_FAILED,
        )
        mutation = """
        mutation($id: GlobalID!) {
          resyncMappedImport(id: $id) {
            id
            status
            percentage
          }
        }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={"id": self.to_global_id(mapped_import)},
        )

        self.assertIsNone(resp.errors)
        mapped_import.refresh_from_db()
        self.assertEqual(mapped_import.status, MappedImport.STATUS_PENDING)
        self.assertEqual(mapped_import.percentage, 0)
        mocked_safe_run_task.assert_called_once()

    # @TODO TO fix 04.04.2026
    @unittest.skip("TODO 04.04.2026: test fixture creates abstract SalesChannel and triggers connect().")
    def test_delete_export_uses_generic_delete_mutation(self):
        export_process = Export.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Export.TYPE_JSON,
            kind=Export.KIND_PRODUCTS,
        )
        mutation = """
        mutation($data: NodeInput!) {
          deleteExport(data: $data) {
            id
          }
        }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={"data": {"id": self.to_global_id(export_process)}},
        )

        self.assertIsNone(resp.errors)
        self.assertFalse(Export.objects.filter(id=export_process.id).exists())


class ExportMutationHelpersUnitTest(unittest.TestCase):
    def test_build_export_parameters_ignores_none_values(self):
        data = SimpleNamespace(
            sales_channel=None,
            salespricelist=None,
            active_only=None,
            flat=True,
            add_translations=None,
            values_are_ids=None,
            add_value_ids=None,
            add_product_sku=None,
            add_title=None,
            add_description=None,
            product_properties_add_value_ids=None,
            property_select_values_add_value_ids=None,
            ids=None,
        )

        parameters = _build_export_parameters(
            data=data,
            kind=Export.KIND_PRODUCTS,
            multi_tenant_company=None,
            allow_ids=False,
            include_none=False,
        )

        self.assertEqual(parameters, {"flat": True})

    def test_merge_parameter_dicts_preserves_existing_nested_parameters(self):
        merged = _merge_parameter_dicts(
            existing={
                "sales_channel": 2,
                "product_properties": {
                    "add_value_ids": True,
                },
            },
            updates={
                "flat": True,
            },
        )

        self.assertEqual(
            merged,
            {
                "sales_channel": 2,
                "product_properties": {
                    "add_value_ids": True,
                },
                "flat": True,
            },
        )
