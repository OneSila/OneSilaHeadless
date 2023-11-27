from strawberry import UNSET
from strawberry_django import auth as strawberry_auth
from strawberry_django.resolvers import django_resolver
from strawberry_django.mutations import resolvers
from strawberry_django.auth.utils import get_current_user
from strawberry_django.optimizer import DjangoOptimizerExtension
from strawberry_django.utils.requests import get_request
from strawberry_django.auth.exceptions import IncorrectUsernamePasswordError

from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib import auth
from django.contrib.auth.password_validation import validate_password
from django.db.utils import IntegrityError
from django.conf import settings

from typing import cast, Type
from asgiref.sync import async_to_sync, sync_to_async

from channels import auth as channels_auth
from channels.db import database_sync_to_async

from core.schema.core.mutations import create, type, DjangoUpdateMutation, \
    DjangoCreateMutation, GetMultiTenantCompanyMixin, default_extensions, \
    update, Info, models, Iterable, Any, IsAuthenticated
from core.schema.core.mixins import GetQuerysetMultiTenantMixin
from core.factories.multi_tenant import InviteUserFactory, RegisterUserFactory

from .types.types import MultiTenantUserType, MultiTenantCompanyType
from .types.input import MultiTenantUserInput, MultiTenantUserPartialInput, \
    MultiTenantCompanyPartialInput, MultiTenantCompanyInput, \
    MultiTenantInviteUserInput, MultiTenantCompanyMyInput


class CleanupDataMixin:
    def cleanup_data(self, data):
        for k in data.copy().keys():
            if data[k] is UNSET:
                del data[k]

        return data


class RegisterUserMutation(CleanupDataMixin, DjangoCreateMutation):
    AUTO_LOGIN = settings.STRAWBERRY_DJANGO_REGISTER_USER_AUTO_LOGIN

    def create_user(self, data):
        data = self.cleanup_data(data)
        fac = RegisterUserFactory(**data)
        fac.run()

        return fac.user

    def login_user(self, info, username, password):
        request = get_request(info)
        user = auth.authenticate(request, username=username, password=password)

        if user is None:
            raise IncorrectUsernamePasswordError()

        scope = request.consumer.scope
        async_to_sync(channels_auth.login)(scope, user)
        # Channels docs, you must save the session, or no user will be logged in.
        scope["session"].save()

        return user

    def create(self, data: dict[str, Any], *, info: Info):
        password = data.get("password")
        username = data.get('username')
        validate_password(password)

        with DjangoOptimizerExtension.disabled():
            user = self.create_user(data)

            if self.AUTO_LOGIN:
                # FIXME: Using auto-login seems to break:
                # https://stackoverflow.com/questions/77557246/django-channels-login-connection-already-closed
                # breaks on async_to_sync(channels_auth.login) section.
                self.login_user(info, username, password)

            return user


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


class AcceptInvitationMutation(DjangoUpdateMutation):
    pass


class MyMultiTenantCompanyCreateMutation(GetMultiTenantCompanyMixin, DjangoCreateMutation):
    def create(self, data: dict[str, Any], *, info: Info):
        model = self.django_model
        assert model is not None

        user = get_current_user(info)

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
        assert model is not None

        data: Any = kwargs.get(self.argument_name)
        vdata = vars(data).copy() if data is not None else {}
        instance = self.get_multi_tenant_company(info)

        return self.update(info, instance, resolvers.parse_input(info, vdata))


class UpdateMeMutation(DjangoUpdateMutation):
    @django_resolver
    @transaction.atomic
    def resolver(self, source: Any, info: Info, args: list[Any], kwargs: dict[str, Any],) -> Any:
        model = self.django_model
        assert model is not None

        data: Any = kwargs.get(self.argument_name)
        vdata = vars(data).copy() if data is not None else {}
        instance = get_current_user(info)

        return self.update(info, instance, resolvers.parse_input(info, vdata))


def register_my_multi_tenant_company():
    extensions = [IsAuthenticated()]
    return MyMultiTenantCompanyCreateMutation(MultiTenantCompanyMyInput, extensions=extensions)


def update_my_multi_tenant_company():
    extensions = default_extensions
    return MyMultiTentantCompanyUpdateMutation(MultiTenantCompanyPartialInput, extensions=extensions)


def update_me():
    extensions = default_extensions
    return UpdateMeMutation(MultiTenantUserPartialInput, extensions=extensions)


def register_user():
    extensions = []
    return RegisterUserMutation(MultiTenantUserInput, extensions=extensions)


def invite_user():
    extensions = default_extensions
    return InviteUserMutation(MultiTenantInviteUserInput, extensions=extensions)


@type(name="Mutation")
class MultiTenantMutation:
    login: MultiTenantUserType = strawberry_auth.login()
    logout = strawberry_auth.logout()

    register_user: MultiTenantUserType = register_user()
    register_my_multi_tenant_company: MultiTenantCompanyType = register_my_multi_tenant_company()

    update_me: MultiTenantUserType = update_me()
    update_my_multi_tenant_company: MultiTenantCompanyType = update_my_multi_tenant_company()

    invite_user: MultiTenantUserType = invite_user()
    # TODO: Invite user mutation.
    # this mutation will:
    # create "un-activated" user
    # assign to multi-tenant-company
    # send out email to invite and resturn invitation link
    # + query/mutation flow for the user to actually subscribe.
    # + mutation to re-invite the user
