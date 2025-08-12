from media.models import Media
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
