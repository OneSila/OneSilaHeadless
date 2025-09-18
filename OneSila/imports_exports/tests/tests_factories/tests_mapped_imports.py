import json
import tempfile
from django.core.files.base import ContentFile
from core.tests import TestCase
from imports_exports.models import MappedImport


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
