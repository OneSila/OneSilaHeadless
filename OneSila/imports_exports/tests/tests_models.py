from django.core.files.base import ContentFile
from imports_exports.models import Import, MappedImport
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
