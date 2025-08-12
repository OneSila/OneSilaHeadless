from media.models import Media, Image
from core.tests import TestCase
from model_bakery import baker
from django.core.files import File
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
