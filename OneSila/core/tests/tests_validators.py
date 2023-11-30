from django.core.files import File
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.conf import settings
from core.models.multi_tenant import MultiTenantUser
import os


class ValidatorTestCase(TestCase):
    def setUp(self):
        self.user = MultiTenantUser.objects.create(username='test_validator@mail.com')
        self.user.set_password('someFake11!1id3')
        self.user.save()

        self.image_path = os.path.join(settings.BASE_DIR.parent, 'core', 'tests', 'image_files')

    def test_valid_imagefile(self):
        fname = 'red.png'
        fpath = os.path.join(self.image_path, fname)

        with open(fpath, 'rb') as f:
            try:
                self.user.avatar.save(fname, File(f))
                self.user.full_clean()
                self.user.save()
            except Exception:
                self.fail("png files without dot should be allowed.")

    def test_invalid_extension(self):
        fname = 'red.psd'
        fpath = os.path.join(self.image_path, fname)

        with open(fpath, 'rb') as f:
            try:
                self.user.avatar.save(fname, File(f))
                self.user.full_clean()
                self.user.save()
                self.fail('should not be able to save a psd file.')
            except ValidationError:
                pass

    def test_with_dots(self):
        fname = 'red.with.dots.png'
        fpath = os.path.join(self.image_path, fname)

        with open(fpath, 'rb') as f:
            try:
                self.user.avatar.save(fname, File(f))
                self.user.full_clean()
                self.user.save()
                self.fail('should not be able to save a filename with dots')
            except ValidationError:
                pass
