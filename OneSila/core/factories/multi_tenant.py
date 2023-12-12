from django.db import transaction
from core.models.multi_tenant import MultiTenantUser, MultiTenantUserLoginToken
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

from core.signals import registered, invite_sent, invite_accepted, \
    disabled, enabled, login_token_created, recovery_token_created


class AuthenticateTokenFactory:
    def __init__(self, token, info):
        self.info = info
        self.token = token

    def set_token_instance(self):
        self.token_instance = MultiTenantUserLoginToken.objects.get_by_token(self.token)

    def set_user(self):
        self.user = self.token_instance.multi_tenant_user

    def run(self):
        self.set_token_instance()
        self.set_user()


class LoginTokenFactory:
    def __init__(self, user):
        self.user = user

    def create_token(self):
        self.token = MultiTenantUserLoginToken.objects.create(
            multi_tenant_user=self.user)

    def send_signal(self):
        login_token_created.send(sender=self.token.__class__, instance=self.token)

    def run(self):
        self.create_token()


class RecoveryTokenFactory(LoginTokenFactory):
    def send_signal(self):
        recovery_token_created.send(sender=self.token.__class__, instance=self.token)


class RegisterUserFactory:
    model = MultiTenantUser
    is_multi_tenant_company_owner = True
    invitation_accepted = True

    def __init__(self, *, username, password, language, first_name="", last_name=""):
        self.username = username
        self.password = password
        self.language = language
        self.first_name = first_name
        self.last_name = last_name

    def validate_password(self):
        validate_password(password=self.password)

    def create_user(self):
        user = self.model(
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name,
            language=self.language
        )

        try:
            user.full_clean()
        except ValidationError as e:
            if 'username' in str(e):
                raise Exception("Email is already taken.")

        user.set_password(self.password)
        user.save()

        self.user = user

    def send_signal(self):
        registered.send(sender=self.user.__class__, instance=self.user)

    @transaction.atomic
    def run(self):
        self.validate_password()
        self.create_user()
        self.send_signal()


class InviteUserFactory:
    model = MultiTenantUser
    invitation_accepted = False
    is_active = False

    def __init__(self, *, multi_tenant_company, language, username, first_name="", last_name=""):
        self.multi_tenant_company = multi_tenant_company
        self.language = language
        self.username = username
        self.first_name = first_name
        self.last_name = last_name

    @transaction.atomic
    def create_user(self):
        user = self.model(
            multi_tenant_company=self.multi_tenant_company,
            language=self.language,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name,
            is_active=self.is_active,
            invitation_accepted=self.invitation_accepted,
        )

        try:
            user.full_clean()
        except ValidationError as e:
            if 'username' in str(e):
                raise Exception("Email is already taken.")

        user.save()
        self.user = user

    def send_signal(self):
        invite_sent.send(sender=self.user.__class__, instance=self.user)

    @transaction.atomic
    def run(self):
        self.create_user()
        self.send_signal()


class AcceptUserInviteFactory:
    def __init__(self, user, password, language):
        self.user = user

        self.password = password
        self.language = language

    def update_user(self):
        self.user.invitation_accepted = True
        self.user.language = self.language
        self.user.is_active = True

        self.user.set_password(self.password)
        self.user.save()

    def send_signal(self):
        invite_accepted.send(sender=self.user.__class__, instance=self.user)

    @transaction.atomic
    def run(self):
        self.update_user()
        self.send_signal()


class DisableUserFactory:
    def __init__(self, user):
        self.user = user

    def disable_user(self):
        self.user.set_inactive()

    def send_signal(self):
        disabled.send(sender=self.user.__class__, instance=self.user)

    @transaction.atomic
    def run(self):
        self.disable_user()
        self.send_signal()


class EnableUserFactory:
    def __init__(self, user):
        self.user = user

    def enable_user(self):
        self.user.set_active()

    def send_signal(self):
        enabled.send(sender=self.user.__class__, instance=self.user)

    @transaction.atomic
    def run(self):
        self.enable_user()
        self.send_signal()
