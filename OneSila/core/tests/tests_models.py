from django.utils import timezone
from django.core.files import File
from django.conf import settings
import os

from core.models.multi_tenant import MultiTenantUserLoginToken
from core.tests import TestCase
from model_bakery import baker


class TestMultiTenantUserLoginTokenTestCase(TestCase):
    def setUp(self):
        self.user = baker.make('core.MultiTenantUser')

    def test_expired_token(self):
        token = baker.make("core.MultiTenantUserLoginToken")
        past = timezone.now() - timezone.timedelta(minutes=MultiTenantUserLoginToken.EXPIRES_AFTER_MIN + 1)
        token.set_expires_at(expires_at=past)
        token.refresh_from_db()
        self.assertFalse(token.is_valid())

    def test_almost_expired_token(self):
        token = baker.make("core.MultiTenantUserLoginToken")
        present = timezone.now()
        token.set_expires_at(expires_at=present)
        token.refresh_from_db()

        self.assertTrue(token.is_valid())

    def test_valid_token(self):
        token = baker.make("core.MultiTenantUserLoginToken")
        token.set_expires_at()
        token.refresh_from_db()

        self.assertTrue(token.expires_at is not None)
        self.assertTrue(token.is_valid())


class TestMultiTenantUserAvatarUploadPath(TestCase):
    def test_avatar_upload_path(self):
        image_path = os.path.join(settings.BASE_DIR.parent, 'core', 'tests', 'image_files', 'red.png')
        with open(image_path, 'rb') as f:
            self.user.avatar.save('red.png', File(f))
        parts = self.user.avatar.name.split('/')
        self.assertEqual(parts[0], str(self.multi_tenant_company.id))
        self.assertEqual(parts[1], 'avatars')
        self.assertEqual(len(parts), 8)
