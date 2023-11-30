from django.core.files import File
from django.test import TestCase
from django.conf import settings
from core.models.multi_tenant import MultiTenantUser
import os


class ValidatorTestCase(TestCase):
    def setUp(self):
        self.user = MultiTenantUser.objects.create(username='test_validator@mail.com')
        self.image_path = os.path.join(settings.BASE_DIR.parent, 'core', 'tests', 'image_files')

    def test_valid_imagefile(self):
        fname = 'red.png'
        fpath = os.path.join(self.image_path, fname)

        with open(fpath, 'rb') as f:
            self.user.avatar.save(fname, File(f))
            self.user.save()

    def test_invalid_extension(self):
        fname = 'red.psd'
        fpath = os.path.join(self.image_path, fname)

        with open(fpath, 'rb') as f:
            self.user.avatar.save(fname, File(f))
            self.user.save()

    def test_with_dots(self):
        fname = 'red.with.dots.png'
        fpath = os.path.join(self.image_path, fname)

        with open(fpath, 'rb') as f:
            self.user.avatar.save(fname, File(f))
            self.user.save()
