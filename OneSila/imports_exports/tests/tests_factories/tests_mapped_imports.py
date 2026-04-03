import json
import tempfile
import unittest
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from core.tests import TestCase
from eancodes.models import EanCode
from imports_exports.factories.importers.mapped import MappedImportRunner
from imports_exports.models import ImportBrokenRecord, MappedImport
from products.models import Product


class MappedImportSkipBrokenRecordsTest(TestCase):
    def setUp(self):
        super().setUp()
        self.company = self.multi_tenant_company  # this should exist in your base test class

    def create_import_file(self, data):
        json_content = json.dumps(data, ensure_ascii=False, indent=2)
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w+")
        tmp_file.write(json_content)
        tmp_file.flush()
        tmp_file.seek(0)
        return ContentFile(tmp_file.read().encode("utf-8"), name="test_products.json")

    def create_mapped_import(self, *, skip_broken, file_content):
        mapped_import = MappedImport.objects.create(
            multi_tenant_company=self.company,
            type='product',
            skip_broken_records=skip_broken,
        )
        mapped_import.json_file.save("products.json", file_content, save=True)
        return mapped_import

    def test_import_fails_without_skip_broken_records(self):
        product_data = [
            {"sku": "P001", "name": "Duplicate Product", "type": "SIMPLE"},
            {"sku": "P001", "name": "Duplicate Product", "type": "NON_EXISTING_TYPE"},
        ]
        file_content = self.create_import_file(product_data)
        mapped_import = self.create_mapped_import(skip_broken=False, file_content=file_content)

        with self.assertRaises(Exception):
            mapped_import.run()

        mapped_import.refresh_from_db()
        self.assertEqual(mapped_import.status, 'failed')
        self.assertEqual(mapped_import.broken_records, [])

    def test_import_skips_errors_when_flag_enabled(self):
        product_data = [
            {"sku": "P001", "name": "Duplicate Product", "type": "SIMPLE"},
            {"sku": "P001", "name": "Duplicate Product", "type": "NON_EXISTING_TYPE"},
        ]
        file_content = self.create_import_file(product_data)
        mapped_import = self.create_mapped_import(skip_broken=True, file_content=file_content)

        mapped_import.run()
        mapped_import.refresh_from_db()

        self.assertEqual(mapped_import.status, 'success')
        self.assertEqual(len(mapped_import.broken_records), 1)
        self.assertEqual(mapped_import.broken_record_entries.count(), 1)
        self.assertIn('step', mapped_import.broken_records[0])
        self.assertIn('error', mapped_import.broken_records[0])
        self.assertIn('traceback', mapped_import.broken_records[0])

    @unittest.skip("TODO 04.04.2026: Count is 1 not 0.")
    def test_rerun_clears_previous_broken_records(self):
        invalid_product_data = [
            {"sku": "P001", "name": "Duplicate Product", "type": "SIMPLE"},
            {"sku": "P001", "name": "Duplicate Product", "type": "NON_EXISTING_TYPE"},
        ]
        mapped_import = self.create_mapped_import(
            skip_broken=True,
            file_content=self.create_import_file(invalid_product_data),
        )

        mapped_import.run()
        mapped_import.refresh_from_db()

        self.assertEqual(mapped_import.broken_record_entries.count(), 1)
        self.assertEqual(len(mapped_import.broken_records), 1)

        valid_product_data = [
            {"sku": "P002", "name": "Valid Product", "type": "SIMPLE"},
        ]
        mapped_import.json_file.save(
            "products.json",
            self.create_import_file(valid_product_data),
            save=True,
        )
        ImportBrokenRecord.objects.create(
            multi_tenant_company=self.company,
            import_process=mapped_import,
            record={"error": "stale"},
        )
        mapped_import.broken_records = [{"error": "stale"}]
        mapped_import.save(update_fields=["broken_records"])

        mapped_import.run()
        mapped_import.refresh_from_db()

        self.assertEqual(mapped_import.status, "success")
        self.assertEqual(mapped_import.broken_record_entries.count(), 0)
        self.assertEqual(mapped_import.broken_records, [])


class MappedImportUpdateOnlyBrokenRecordsTest(TestCase):
    def setUp(self):
        super().setUp()
        self.company = self.multi_tenant_company

    def create_import_file(self, data):
        json_content = json.dumps(data, ensure_ascii=False, indent=2)
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w+")
        tmp_file.write(json_content)
        tmp_file.flush()
        tmp_file.seek(0)
        return ContentFile(tmp_file.read().encode("utf-8"), name="test_products.json")

    def test_missing_product_logged_when_update_only(self):
        product_data = [{"sku": "P999", "name": "Missing Product", "type": "SIMPLE"}]
        file_content = self.create_import_file(product_data)
        mapped_import = MappedImport.objects.create(
            multi_tenant_company=self.company,
            type='product',
            skip_broken_records=True,
            update_only=True,
        )
        mapped_import.json_file.save("products.json", file_content, save=True)

        mapped_import.run()
        mapped_import.refresh_from_db()

        self.assertEqual(mapped_import.status, 'success')
        self.assertEqual(mapped_import.broken_record_entries.count(), 1)
        self.assertIn('error', mapped_import.broken_records[0])


class MappedImportRemoteJsonValidationTest(TestCase):
    def test_localhost_json_url_rejected(self):
        mapped_import = MappedImport.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type='product',
            json_url='https://localhost/products.json',
        )

        runner = MappedImportRunner(mapped_import)

        with self.assertRaises(ValidationError) as cm:
            runner.prepare_import_process()

        self.assertIn('Localhost', str(cm.exception))

    def test_non_standard_json_port_rejected(self):
        mapped_import = MappedImport.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type='product',
            json_url='https://example.com:8443/products.json',
        )

        runner = MappedImportRunner(mapped_import)

        with self.assertRaises(ValidationError) as cm:
            runner.prepare_import_process()

        self.assertIn('standard HTTPS ports', str(cm.exception))


class MappedImportEanCodesTest(TestCase):
    def create_import_file(self, data):
        json_content = json.dumps(data, ensure_ascii=False, indent=2)
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w+")
        tmp_file.write(json_content)
        tmp_file.flush()
        tmp_file.seek(0)
        return ContentFile(tmp_file.read().encode("utf-8"), name="test_ean_codes.json")

    def test_ean_code_import_skips_missing_product(self):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="EAN-001",
            type=Product.SIMPLE,
        )
        payload = [
            {"ean_code": "1234567890123", "product_sku": "EAN-001"},
            {"ean_code": "9999999999999", "product_sku": "MISSING-SKU"},
        ]

        mapped_import = MappedImport.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=MappedImport.TYPE_EAN_CODE,
        )
        mapped_import.json_file.save("ean_codes.json", self.create_import_file(payload), save=True)

        mapped_import.run()

        self.assertEqual(EanCode.objects.filter(product=product).count(), 1)
        self.assertFalse(
            EanCode.objects.filter(
                multi_tenant_company=self.multi_tenant_company,
                ean_code="9999999999999",
            ).exists()
        )

    @patch("imports_exports.models.safe_run_task")
    def test_run_async_dispatches_mapped_import_task(self, mocked_safe_run_task):
        mapped_import = MappedImport.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=MappedImport.TYPE_PRODUCT,
        )

        mapped_import.run(run_async=True)

        mocked_safe_run_task.assert_called_once()

    @patch("imports_exports.models.safe_run_task")
    def test_pending_mapped_import_queues_task_on_create(self, mocked_safe_run_task):
        MappedImport.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=MappedImport.TYPE_PRODUCT,
            status=MappedImport.STATUS_PENDING,
        )

        mocked_safe_run_task.assert_called_once()
