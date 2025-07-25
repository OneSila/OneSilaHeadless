from media.models import Media
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
