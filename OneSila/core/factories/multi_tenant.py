from django.db import transaction
from core.models.multi_tenant import MultiTenantUser
from django.core.exceptions import ValidationError


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

    def send_welcome(self):
        pass

    @transaction.atomic
    def run(self):
        self.create_user()
        self.send_welcome()


class InviteUserFactory:
    model = MultiTenantUser
    is_active = False
    invitation_accepted = False

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

    def send_invite(self):
        # FIXME: Send out (branded) email to the new user.
        pass

    @transaction.atomic
    def run(self):
        self.create_user()
        self.send_invite()
