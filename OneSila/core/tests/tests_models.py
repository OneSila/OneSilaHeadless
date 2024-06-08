from django.utils import timezone

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
