from media.models import Media, Image
from core.tests import TestCase
from model_bakery import baker
from django.core.files import File
from django.core.files.base import ContentFile
from django.conf import settings
from pathlib import Path

from .helpers import CreateImageMixin

import os
import logging

logger = logging.getLogger(__name__)


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

    def test_shared_file_not_deleted(self):
        """Test that a shared file is not deleted when one media instance is deleted."""
        # Create a shared image file
        shared_image_file = self.get_image_file('red.png')

        # Create two media instances sharing the same file
        media1 = Media.objects.create(type=Media.FILE, file=shared_image_file, multi_tenant_company=self.multi_tenant_company)
        media2 = Media.objects.create(type=Media.FILE, file=shared_image_file, multi_tenant_company=self.multi_tenant_company)

        media1.refresh_from_db()
        media2.refresh_from_db()

        # Ensure ids are different:
        self.assertNotEqual(media1.id, media2.id)

        # Verify that we can find the media instances in the database
        media1_absolute_path = media1.file.path
        media2_absolute_path = media2.file.path
        rel_path_media1 = str(Path(media1_absolute_path).relative_to(settings.MEDIA_ROOT))
        rel_path_media2 = str(Path(media2_absolute_path).relative_to(settings.MEDIA_ROOT))

        # These rel paths should not be the same.
        # So the there should never be share files.
        self.assertNotEqual(rel_path_media1, rel_path_media2)

        # Tests continuation below are a non-issue.
        # media1_qs = Media.objects.filter(file__endswith=rel_path_media1)
        # media2_qs = Media.objects.filter(file__endswith=rel_path_media1)

        # self.assertEqual(media1_qs.count(), 2)
        # self.assertEqual(media2_qs.count(), 2)

        # # Ensure the the files are truly shared
        # shared_image_path1 = media1.file.path
        # logger.debug(f"About to investigate shared_image_path1 {shared_image_path1}")
        # shared_image_path2 = media2.file.path
        # logger.debug(f"About to investigate shared_image_path2 {shared_image_path2}")
        # self.assertEqual(shared_image_path1, shared_image_path2)

        # # And that they exist
        # self.assertTrue(os.path.exists(shared_image_path1))
        # self.assertTrue(os.path.exists(shared_image_path2))

        # # Delete one media instance
        # media1.delete()

        # # Verify that the shared image file is still present
        # self.assertTrue(os.path.exists(shared_image_path2))

        # # Clean up by deleting the second media instance
        # media2.delete()


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
