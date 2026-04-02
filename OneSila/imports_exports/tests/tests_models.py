from datetime import datetime
from django.core.files.base import ContentFile
from unittest.mock import patch

from imports_exports.models import Export, Import, MappedImport
from core.tests import TestCase


class MappedImportUploadPathTest(TestCase):
    def test_json_file_upload_path(self):
        mapped_import = MappedImport.objects.create(multi_tenant_company=self.multi_tenant_company)
        mapped_import.json_file.save('data.json', ContentFile(b'{}'))
        parts = mapped_import.json_file.name.split('/')
        self.assertEqual(parts[0], str(self.multi_tenant_company.id))
        self.assertEqual(parts[1], 'mapped_imports')
        self.assertEqual(len(parts), 6)


class ImportStrTest(TestCase):
    def test_str_with_name(self):
        import_process = Import.objects.create(
            multi_tenant_company=self.multi_tenant_company, name="My Import"
        )
        self.assertEqual(str(import_process), "My Import - New (0%)")

    def test_str_without_name(self):
        import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.assertEqual(str(import_process), "ImportProcess - New (0%)")


class ProcessNameDefaultingTest(TestCase):
    @patch("imports_exports.models.timezone.localtime")
    def test_mapped_import_blank_name_defaults_to_now_string(self, mocked_localtime):
        mocked_localtime.return_value = datetime(2026, 4, 2, 20, 55, 0)

        mapped_import = MappedImport.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="   ",
        )

        self.assertEqual(mapped_import.name, "2026-04-02 20:55:00")

    @patch("imports_exports.models.timezone.localtime")
    def test_export_blank_name_defaults_to_now_string(self, mocked_localtime):
        mocked_localtime.return_value = datetime(2026, 4, 2, 20, 56, 0)

        export_process = Export.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            kind=Export.KIND_PROPERTIES,
            name="",
        )

        self.assertEqual(export_process.name, "2026-04-02 20:56:00")
