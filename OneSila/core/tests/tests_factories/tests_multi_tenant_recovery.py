from django.utils import timezone
from django.core.exceptions import ValidationError

from core.tests import TestCase
from core.models.multi_tenant import MultiTenantUserLoginToken
from core.factories.multi_tenant import LoginTokenFactory, AuthenticateTokenFactory, \
    RecoveryTokenFactory


class AccountRecoveryTestCase(TestCase):
    def test_login_token(self):
        fac = LoginTokenFactory(self.user)
        fac.run()

        self.assertTrue(fac.token is not None)

    def test_recovery_token(self):
        fac = RecoveryTokenFactory(self.user)
        fac.run()

        self.assertTrue(fac.token is not None)

    def test_authenticate_token(self):
        fac = LoginTokenFactory(self.user)
        fac.run()
        token = fac.token.token

        fac = AuthenticateTokenFactory(token)
        fac.run()

        self.assertTrue(fac.user is not None)

    def test_invalid_token(self):
        try:
            fac = AuthenticateTokenFactory('fake_token')
            fac.run()

            self.fail("Shouldn't be able to login with a fake token")
        except ValidationError:
            pass

    def test_expired_token(self):
        hours = (MultiTenantUserLoginToken.EXPIRES_AFTER_MIN + 1) / 60

        try:
            fac = LoginTokenFactory(self.user)
            fac.run()
            token = fac.token

            # Update via bulk, otherwise the save() method will reset the expires_at value
            tokens = MultiTenantUserLoginToken.objects.filter(id=token.id)
            tokens.update(expires_at=token.created_at - timezone.timedelta(hours=hours))
            token.refresh_from_db()

            fac = AuthenticateTokenFactory(token)
            fac.run()

            self.fail("Shouldn't be able to login with an expired token")
        except ValidationError:
            pass
