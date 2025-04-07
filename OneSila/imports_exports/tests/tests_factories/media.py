from core.tests import TestCase
from imports_exports.factories.media import ImportImageInstance
from imports_exports.models import Import
from media.models import Image, MediaProductThrough, Media
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
        through_exists = MediaProductThrough.objects.filter(
            product=product,
            media=instance.instance
        ).exists()

        self.assertTrue(through_exists)

    def test_given_product_image_attached(self):
        data = {
            "image_url": "https://vgl.ucdavis.edu/sites/g/files/dgvnsk15116/files/styles/sf_landscape_4x3/public/images/marketing_highlight/Sample-Collection-Box-Cat-640px.jpg"
        }

        instance = ImportImageInstance(data, self.import_process, product=self.product)
        instance.multi_tenant_company = self.import_process.multi_tenant_company
        instance.process()

        through_exists = MediaProductThrough.objects.filter(
            product=self.product,
            media=instance.instance
        ).exists()

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

    def test_non_image_content_type(self):
        data = {
            "image_url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
        }

        instance = ImportImageInstance(data, self.import_process)
        instance.multi_tenant_company = self.import_process.multi_tenant_company
        instance.process()

        self.assertNotIn("image", instance.kwargs)
        self.assertIsNone(instance.instance)