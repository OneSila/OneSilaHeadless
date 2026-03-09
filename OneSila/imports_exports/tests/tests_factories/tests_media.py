from unittest.mock import Mock, patch

from core.tests import TestCase
from django.core.exceptions import ValidationError
from imports_exports.factories.media import ImportDocumentInstance, ImportImageInstance
from imports_exports.models import Import
from media.models import DocumentType, Image, MediaProductThrough, Media
from products.models import Product
import base64


class ImportImageInstanceValidateTest(TestCase):

    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

        # Create a sample product
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="SKU123"
        )

        self.sample_base64 = base64.b64encode(b"fake-image-content").decode("utf-8")

    def test_validate_with_image_url(self):
        data = {
            "image_url": "https://example.com/image.png"
        }
        instance = ImportImageInstance(data, self.import_process)
        self.assertEqual(instance.image_url, "https://example.com/image.png")

    def test_validate_with_image_content(self):
        data = {
            "image_content": self.sample_base64
        }
        instance = ImportImageInstance(data, self.import_process)
        self.assertEqual(instance.image_content, self.sample_base64)

    def test_validate_with_image_url_and_image_content(self):
        data = {
            "image_url": "https://example.com/valid.png",
            "image_content": self.sample_base64
        }
        instance = ImportImageInstance(data, self.import_process)
        self.assertEqual(instance.image_url, "https://example.com/valid.png")
        self.assertEqual(instance.image_content, self.sample_base64)

    def test_missing_both_image_url_and_content_raises(self):
        data = {
            "type": "PACK_SHOT"
        }
        with self.assertRaises(ValueError) as cm:
            ImportImageInstance(data, self.import_process)
        self.assertIn("Either 'image_url' or 'image_content' must be provided", str(cm.exception))

    def test_sets_default_type_and_sort_order(self):
        data = {
            "image_content": self.sample_base64
        }
        instance = ImportImageInstance(data, self.import_process)
        self.assertEqual(instance.type, Image.PACK_SHOT)
        self.assertEqual(instance.sort_order, 10)
        self.assertFalse(instance.is_main_image)

    def test_sets_is_main_image_true(self):
        data = {
            "image_content": self.sample_base64,
            "is_main_image": True,
            "sort_order": 1
        }
        instance = ImportImageInstance(data, self.import_process)
        self.assertTrue(instance.is_main_image)
        self.assertEqual(instance.sort_order, 1)

    def test_with_associated_product(self):
        data = {
            "image_content": self.sample_base64,
            "product_data": {
                "name": "Image Product",
                "sku": "SKU_IMAGE"
            }
        }
        instance = ImportImageInstance(data, self.import_process)
        self.assertIsNotNone(instance.product_import_instance)


class ImportImageInstanceProcessTest(TestCase):
    def setUp(self):

        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

        self.product = Product.objects.create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sku="IMG001",
            type=Product.SIMPLE
        )

    def test_without_product_valid_https_image(self):
        data = {
            "image_url": "https://2.img-dpreview.com/files/p/E~C1000x0S4000x4000T1200x1200~articles/3925134721/0266554465.jpeg"
        }

        instance = ImportImageInstance(data, self.import_process)
        instance.multi_tenant_company = self.import_process.multi_tenant_company
        instance.process()

        self.assertIsNotNone(instance.instance)
        self.assertEqual(instance.instance.type, Media.IMAGE)

    def test_product_data_image_attached(self):
        data = {
            "image_url": "https://2.img-dpreview.com/files/p/E~C1000x0S4000x4000T1200x1200~articles/3925134721/0266554465.jpeg",
            "product_data": {
                "name": "Product With Image",
                "sku": "IMG002"
            }
        }

        instance = ImportImageInstance(data, self.import_process)
        instance.multi_tenant_company = self.import_process.multi_tenant_company
        instance.process()

        product = Product.objects.get(sku="IMG002")
        through_exists = MediaProductThrough.objects.get_product_images(
            product=product,
            sales_channel=None,
        ).filter(media=instance.instance).exists()

        self.assertTrue(through_exists)

    def test_given_product_image_attached(self):
        data = {
            "image_url": "https://vgl.ucdavis.edu/sites/g/files/dgvnsk15116/files/styles/sf_landscape_4x3/public/images/marketing_highlight/Sample-Collection-Box-Cat-640px.jpg"
        }

        instance = ImportImageInstance(data, self.import_process, product=self.product)
        instance.multi_tenant_company = self.import_process.multi_tenant_company
        instance.process()

        through_exists = MediaProductThrough.objects.get_product_images(
            product=self.product,
            sales_channel=None,
        ).filter(media=instance.instance).exists()

        self.assertTrue(through_exists)

    def test_non_existent_url(self):
        data = {
            "image_url": "https://example.com/nonexistent.jpg"
        }

        instance = ImportImageInstance(data, self.import_process)
        instance.multi_tenant_company = self.import_process.multi_tenant_company
        instance.process()

        self.assertTrue(instance.skip_create)
        self.assertIsNone(instance.instance)

    def test_http_url_rejected(self):
        data = {
            "image_url": "http://example.com/image.jpg"
        }

        instance = ImportImageInstance(data, self.import_process)
        instance.multi_tenant_company = self.import_process.multi_tenant_company
        instance.process()

        self.assertTrue(instance.skip_create)
        self.assertIsNone(instance.instance)

    def test_non_standard_https_port_rejected(self):
        data = {
            "image_url": "https://example.com:8443/image.jpg"
        }

        instance = ImportImageInstance(data, self.import_process)
        instance.multi_tenant_company = self.import_process.multi_tenant_company
        instance.process()

        self.assertTrue(instance.skip_create)
        self.assertIsNone(instance.instance)

    def test_localhost_url_rejected(self):
        data = {
            "image_url": "https://localhost/image.jpg"
        }

        instance = ImportImageInstance(data, self.import_process)
        instance.multi_tenant_company = self.import_process.multi_tenant_company
        instance.process()

        self.assertTrue(instance.skip_create)
        self.assertIsNone(instance.instance)

    def test_loopback_ip_rejected(self):
        data = {
            "image_url": "https://127.0.0.1/image.jpg"
        }

        instance = ImportImageInstance(data, self.import_process)
        instance.multi_tenant_company = self.import_process.multi_tenant_company
        instance.process()

        self.assertTrue(instance.skip_create)
        self.assertIsNone(instance.instance)

    def test_private_ip_rejected(self):
        data = {
            "image_url": "https://10.0.0.5/image.jpg"
        }

        instance = ImportImageInstance(data, self.import_process)
        instance.multi_tenant_company = self.import_process.multi_tenant_company
        instance.process()

        self.assertTrue(instance.skip_create)
        self.assertIsNone(instance.instance)

    def test_non_image_content_type(self):
        data = {
            "image_url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
        }

        instance = ImportImageInstance(data, self.import_process)
        instance.multi_tenant_company = self.import_process.multi_tenant_company
        instance.process()

        self.assertNotIn("image", instance.kwargs)
        self.assertIsNone(instance.instance)


class ImportDocumentInstanceValidateTest(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

    def test_validate_with_document_url(self):
        data = {"document_url": "https://example.com/certificate.pdf"}
        instance = ImportDocumentInstance(data, self.import_process)
        self.assertEqual(instance.document_url, "https://example.com/certificate.pdf")

    def test_missing_document_url_raises(self):
        data = {"title": "Missing URL"}
        with self.assertRaises(ValueError) as cm:
            ImportDocumentInstance(data, self.import_process)
        self.assertIn("document_url", str(cm.exception))

    def test_http_url_rejected(self):
        data = {"document_url": "http://example.com/certificate.pdf"}
        with self.assertRaises(ValidationError) as cm:
            ImportDocumentInstance(data, self.import_process)
        self.assertIn("HTTPS", str(cm.exception))

    def test_non_standard_https_port_rejected(self):
        data = {"document_url": "https://example.com:8443/certificate.pdf"}
        with self.assertRaises(ValidationError) as cm:
            ImportDocumentInstance(data, self.import_process)
        self.assertIn("standard HTTPS ports", str(cm.exception))

    def test_localhost_url_rejected(self):
        data = {"document_url": "https://localhost/certificate.pdf"}
        with self.assertRaises(ValidationError) as cm:
            ImportDocumentInstance(data, self.import_process)
        self.assertIn("Localhost", str(cm.exception))

    def test_private_ip_url_rejected(self):
        data = {"document_url": "https://10.0.0.5/certificate.pdf"}
        with self.assertRaises(ValidationError) as cm:
            ImportDocumentInstance(data, self.import_process)
        self.assertIn("Private or reserved IP addresses", str(cm.exception))

    def test_invalid_extension_rejected(self):
        data = {"document_url": "https://example.com/certificate.exe"}
        with self.assertRaises(ValueError) as cm:
            ImportDocumentInstance(data, self.import_process)
        self.assertIn("Unsupported document extension", str(cm.exception))


class ImportDocumentInstanceProcessTest(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.product = Product.objects.create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sku="DOC001",
            type=Product.SIMPLE,
        )

    def _mock_response(self, *, content_type: str, content: bytes):
        response = Mock()
        response.headers = {"Content-Type": content_type}
        response.raise_for_status = Mock()
        response.iter_content = Mock(return_value=[content])
        return response

    @patch("imports_exports.factories.media.requests.get")
    def test_pdf_document_is_imported_and_attached(self, mock_get):
        mock_get.return_value = self._mock_response(
            content_type="application/pdf",
            content=b"%PDF-1.7 test",
        )

        local_type = DocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="Compliance",
            code="COMPLIANCE",
        )
        data = {
            "document_url": "https://example.com/compliance.pdf",
            "document_type": local_type.code,
            "title": "Compliance PDF",
            "sort_order": 5,
        }

        instance = ImportDocumentInstance(data, self.import_process, product=self.product)
        instance.process()

        self.assertIsNotNone(instance.instance)
        self.assertEqual(instance.instance.type, Media.FILE)
        self.assertEqual(instance.instance.original_url, data["document_url"])
        self.assertEqual(instance.instance.document_type_id, local_type.id)
        self.assertFalse(instance.instance.is_document_image)

        through = MediaProductThrough.objects.filter(product=self.product, media=instance.instance).first()
        self.assertIsNotNone(through)
        self.assertEqual(through.sort_order, 5)

    @patch("imports_exports.factories.media.requests.get")
    def test_image_document_sets_is_document_image_and_image_field(self, mock_get):
        mock_get.return_value = self._mock_response(
            content_type="image/jpeg",
            content=b"fake-jpeg",
        )

        data = {
            "document_url": "https://example.com/certificate.jpg",
        }
        instance = ImportDocumentInstance(data, self.import_process, product=self.product)
        instance.process()
        instance.instance.refresh_from_db()

        self.assertTrue(instance.instance.is_document_image)
        self.assertIsNotNone(instance.instance.image)
        self.assertEqual(instance.instance.type, Media.FILE)

    @patch("imports_exports.factories.media.requests.get")
    def test_missing_document_type_defaults_to_internal(self, mock_get):
        mock_get.return_value = self._mock_response(
            content_type="application/pdf",
            content=b"%PDF-1.7 internal-default",
        )

        data = {
            "document_url": "https://example.com/internal-default.pdf",
            "document_type": "",
        }
        instance = ImportDocumentInstance(data, self.import_process, product=self.product)
        instance.process()
        instance.instance.refresh_from_db()

        self.assertEqual(instance.instance.document_type.code, DocumentType.INTERNAL_CODE)

    @patch("imports_exports.factories.media.requests.get")
    def test_reuses_existing_document_by_original_url(self, mock_get):
        mock_get.return_value = self._mock_response(
            content_type="application/pdf",
            content=b"%PDF-1.7 reused",
        )
        data = {"document_url": "https://example.com/shared.pdf"}

        first = ImportDocumentInstance(data, self.import_process, product=self.product)
        first.process()

        other_product = Product.objects.create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sku="DOC002",
            type=Product.SIMPLE,
        )
        second = ImportDocumentInstance(data, self.import_process, product=other_product)
        second.process()

        self.assertEqual(first.instance.id, second.instance.id)
        self.assertEqual(
            Media.objects.filter(
                multi_tenant_company=self.multi_tenant_company,
                type=Media.FILE,
                original_url=data["document_url"],
            ).count(),
            1,
        )
        self.assertTrue(
            MediaProductThrough.objects.filter(product=other_product, media=first.instance).exists()
        )
