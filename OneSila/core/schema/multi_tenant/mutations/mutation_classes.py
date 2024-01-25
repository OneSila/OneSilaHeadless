from strawberry import UNSET

from strawberry.relay.utils import from_base64
from strawberry_django.resolvers import django_resolver
from strawberry_django.mutations import resolvers
from strawberry_django.optimizer import DjangoOptimizerExtension
from strawberry_django.utils.requests import get_request

from django.contrib import auth
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password


from asgiref.sync import async_to_sync

from channels import auth as channels_auth

from core.schema.core.mixins import GetCurrentUserMixin, GetMultiTenantCompanyMixin
from core.schema.core.mutations import create, type, DjangoUpdateMutation, \
    DjangoCreateMutation, default_extensions, \
    update, Info, models, Iterable, Any, IsAuthenticated
from core.factories.multi_tenant import InviteUserFactory, RegisterUserFactory, \
    AcceptUserInviteFactory, EnableUserFactory, DisableUserFactory, RequestLoginTokenFactory, \
    RecoveryTokenFactory, AuthenticateTokenFactory, ChangePasswordFactory
from core.models.multi_tenant import MultiTenantUser


class CleanupDataMixin:
    def cleanup_data(self, data):
        for k in data.copy().keys():
            if data[k] is UNSET:
                del data[k]

        return data


class RequestLoginTokenMutation(CleanupDataMixin, DjangoCreateMutation):
    def create_token(self, *, user):
        fac = RequestLoginTokenFactory(user)
        fac.run()
        return fac.token

    def create(self, data: dict[str, Any], *, info: Info):
        with DjangoOptimizerExtension.disabled():
            user = MultiTenantUser.objects.get(username=data['username'])
            data = self.cleanup_data(data)
            return self.create_token(user=user)


class InviteUserMutation(CleanupDataMixin, GetMultiTenantCompanyMixin, DjangoCreateMutation):
    def create(self, data: dict[str, Any], *, info: Info):
        multi_tenant_company = self.get_multi_tenant_company(info)
        data = self.cleanup_data(data)

        with DjangoOptimizerExtension.disabled():
            fac = InviteUserFactory(
                multi_tenant_company=multi_tenant_company,
                **data)
            fac.run()
            return fac.user


class RecoveryTokenMutation(RequestLoginTokenMutation):
    def create_token(self, *, user):
        fac = RecoveryTokenFactory(user)
        fac.run()
        return fac.token


class AcceptInvitationMutation(GetCurrentUserMixin, DjangoUpdateMutation):
    def update(self, info: Info, instance: models.Model, data: dict[str, Any]):
        user = self.get_current_user(info)
        language = data['language']
        password = data['password']

        with DjangoOptimizerExtension.disabled():
            fac = AcceptUserInviteFactory(
                user=user,
                password=password,
                language=language)
            fac.run()

            return fac.user


class MyMultiTenantCompanyCreateMutation(GetCurrentUserMixin, DjangoCreateMutation):
    def create(self, data: dict[str, Any], *, info: Info):
        model = self.django_model
        assert model is not None

        user = self.get_current_user(info)

        with DjangoOptimizerExtension.disabled():
            obj = resolvers.create(
                info,
                model,
                data,
                full_clean=self.full_clean,
            )

            user.multi_tenant_company = obj
            user.save()

            return obj


class MyMultiTentantCompanyUpdateMutation(GetMultiTenantCompanyMixin, DjangoUpdateMutation):
    """
    This mutation will only protect against having a multi-tentant company.
    Not the existance on the model, since the MultiTenantCompany has no reference to itself.
    """
    @django_resolver
    @transaction.atomic
    def resolver(self, source: Any, info: Info, args: list[Any], kwargs: dict[str, Any],) -> Any:
        model = self.django_model

        data: Any = kwargs.get(self.argument_name)
        vdata = vars(data).copy() if data is not None else {}
        instance = self.get_multi_tenant_company(info)

        return self.update(info, instance, resolvers.parse_input(info, vdata))


class UpdateMeMutation(GetCurrentUserMixin, DjangoUpdateMutation):
    @django_resolver
    @transaction.atomic
    def resolver(self, source: Any, info: Info, args: list[Any], kwargs: dict[str, Any],) -> Any:
        model = self.django_model
        assert model is not None

        data: Any = kwargs.get(self.argument_name)
        vdata = vars(data).copy() if data is not None else {}
        instance = self.get_current_user(info)

        return self.update(info, instance, resolvers.parse_input(info, vdata))


class UpdateMyPasswordMutation(UpdateMeMutation):
    def update(self, info: Info, instance: models.Model, data: dict[str, Any]):
        with DjangoOptimizerExtension.disabled():
            user = instance
            password = data.get("password")

            fac = ChangePasswordFactory(user=user, password=password)
            fac.run()

            return fac.user


class DisableUserMutation(DjangoUpdateMutation):
    def update(self, info: Info, instance: models.Model, data: dict[str, Any]):
        # Do not optimize anything while retrieving the object to update
        with DjangoOptimizerExtension.disabled():
            fac = DisableUserFactory(user=instance)
            fac.run()
            return fac.user


class EnableUserMutation(DjangoUpdateMutation):
    def update(self, info: Info, instance: models.Model, data: dict[str, Any]):
        # Do not optimize anything while retrieving the object to update
        with DjangoOptimizerExtension.disabled():
            fac = EnableUserFactory(user=instance)
            fac.run()

            instance.refresh_from_db()
            return instance
