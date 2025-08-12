from django.core.files.base import ContentFile
from imports_exports.models import MappedImport
from core.tests import TestCase


class MappedImportUploadPathTest(TestCase):
    def test_json_file_upload_path(self):
        mapped_import = MappedImport.objects.create(multi_tenant_company=self.multi_tenant_company)
        mapped_import.json_file.save('data.json', ContentFile(b'{}'))
        parts = mapped_import.json_file.name.split('/')
        self.assertEqual(parts[0], str(self.multi_tenant_company.id))
        self.assertEqual(parts[1], 'mapped_imports')
        self.assertEqual(len(parts), 8)
