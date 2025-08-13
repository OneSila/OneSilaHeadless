from media.models import Media, Image
from core.tests import TestCase
from model_bakery import baker
from django.core.files import File
from django.core.files.base import ContentFile
from django.conf import settings
import os
from .helpers import CreateImageMixin


class MediaTestCase(CreateImageMixin, TestCase):
    def test_image_web_url_none(self):
        image = baker.make(Media, image=None)
        url = image.image_web_url
        self.assertTrue(url is None)

    def test_image_web_url(self):
        image = self.create_image(fname='red.png', multi_tenant_company=self.multi_tenant_company)
        url = image.image_web_url
        self.assertTrue(url.endswith('.jpg'))
        self.assertTrue(url.startswith('http'))

    def test_onesila_thumbnail_url(self):
        image = self.create_image(fname='red.png', multi_tenant_company=self.multi_tenant_company)
        url = image.onesila_thumbnail_url()
        # Cached images are converted to jpg, no matter what the source.
        self.assertTrue(url.endswith('.jpg'))
        self.assertTrue(url.startswith('http'))

    def test_create_duplicate_media_file_returns_initial_id(self):
        image_file = self.get_image_file('red.png')
        image_file_duplicate = self.get_image_file('red.png')

        media1 = Media.objects.create(type=Media.IMAGE, image=image_file, multi_tenant_company=self.multi_tenant_company)
        media2 = Media.objects.create(type=Media.IMAGE, image=image_file_duplicate, multi_tenant_company=self.multi_tenant_company)

        self.assertEqual(media1.id, media2.id)

        image1 = Image.objects.create(image=image_file, multi_tenant_company=self.multi_tenant_company)
        image2 = Image.objects.create(image=image_file_duplicate, multi_tenant_company=self.multi_tenant_company)

        self.assertEqual(image1.id, image2.id)

    def test_image_upload_path(self):
        image = self.create_image(fname='red.png', multi_tenant_company=self.multi_tenant_company)
        parts = image.image.name.split('/')
        self.assertEqual(parts[0], str(self.multi_tenant_company.id))
        self.assertEqual(parts[1], 'images')
        self.assertEqual(len(parts), 8)

    def test_file_upload_path(self):
        media = Media.objects.create(multi_tenant_company=self.multi_tenant_company, type=Media.FILE)
        media.file.save('test.pdf', ContentFile(b'test'))
        parts = media.file.name.split('/')
        self.assertEqual(parts[0], str(self.multi_tenant_company.id))
        self.assertEqual(parts[1], 'files')
        self.assertEqual(len(parts), 8)


class ImageCleanupTestCase(CreateImageMixin, TestCase):
    def test_image_cleanup(self):
        """This test will create and remove an image. Then verify if both the image file and cached files have been removed from storage."""
        # Create an image
        image = self.create_image(fname='red.png', multi_tenant_company=self.multi_tenant_company)
        image_path = image.image.path
        cached_image_path = image.image_web.path

        # Ensure the image and cached image exist
        self.assertTrue(os.path.exists(image_path))
        self.assertTrue(os.path.exists(cached_image_path))

        # Delete the image
        image.delete()

        # Verify that the image and cached image files are removed
        self.assertFalse(os.path.exists(image_path))
        self.assertFalse(os.path.exists(cached_image_path))
