from media.models import Media
from core.tests import TestCase
from model_bakery import baker
from django.core.files import File
from django.conf import settings
import os


class MediaTestCase(TestCase):
    def test_image_web_url_none(self):
        image = baker.make(Media, image=None)
        url = image.image_web_url()
        self.assertTrue(url is None)

    def test_image_web_url(self):
        fname = 'red.png'
        image_path = os.path.join(settings.BASE_DIR.parent, 'core', 'tests', 'image_files', fname)
        image = baker.make(Media)

        with open(image_path, 'rb') as f:
            image.image.save(fname, File(f))
            image.full_clean()
            image.save()
            url = image.image_web_url()

            # Cached images are converted to jpg, no matter what the source.
            self.assertTrue(url.endswith('.jpg'))
            self.assertTrue(url.startswith('http'))
