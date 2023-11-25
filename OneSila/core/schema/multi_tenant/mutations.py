from strawberry import UNSET
from strawberry_django import auth
from strawberry_django.resolvers import django_resolver
from strawberry_django.mutations import resolvers
from strawberry_django.auth.utils import get_current_user
from strawberry_django.optimizer import DjangoOptimizerExtension

from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.db.utils import IntegrityError

from typing import cast, Type

from core.schema.core.mutations import create, type, DjangoUpdateMutation, \
    DjangoCreateMutation, GetMultiTenantCompanyMixin, default_extensions, \
    update, Info, models, Iterable, Any
from core.schema.core.mixins import GetQuerysetMultiTenantMixin
from core.factories.multi_tenant import InviteUserFactory

from .types.types import MultiTenantUserType, MultiTenantCompanyType
from .types.input import MultiTenantUserInput, MultiTenantUserPartialInput, \
    MultiTenantCompanyPartialInput, MultiTenantCompanyInput, MultiTenantInviteUserInput


class SetDefaultValuesMixin:
    DEFAULT_VALUES = {}

    def set_default_values(self, data):
        data.update(self.DEFAULT_VALUES)
        return data


class RegisterUserMutation(SetDefaultValuesMixin, DjangoCreateMutation):
    DEFAULT_VALUES = {
        'is_multi_tenant_company_owner': True,
        'invitation_accepted': True,
    }

    def create(self, data: dict[str, Any], *, info: Info):
        model = cast(Type["AbstractBaseUser"], self.django_model)
        assert model is not None

        password = data.pop("password")
        validate_password(password)

        data = self.set_default_values(data)

        with DjangoOptimizerExtension.disabled():
            return resolvers.create(
                info,
                model,
                data,
                full_clean=self.full_clean,
                pre_save_hook=lambda obj: obj.set_password(password),
            )


class InviteUserMutation(GetMultiTenantCompanyMixin, DjangoCreateMutation):
    @transaction.atomic
    def create(self, data: dict[str, Any], *, info: Info):
        multi_tenant_company = self.get_multi_tenant_company(info)
        data['multi_tenant_company'] = multi_tenant_company
        data['is_active'] = False

        for k in data.keys():
            if data[k] is UNSET:
                del data[k]

        with DjangoOptimizerExtension.disabled():
            # Lets bother with the resolvers.  We just want to create the item.
            # But we do want to validate before saving.
            fac = InviteUserFactory(
                data=data,
                model=self.django_model)
            fac.run()

            return fac.user


class MyMultiTenantCompanyCreateMutation(GetMultiTenantCompanyMixin, DjangoCreateMutation):
    def create(self, data: dict[str, Any], *, info: Info):
        model = self.django_model
        assert model is not None

        data = self.set_default_values(data)
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
    extensions = default_extensions
    return MyMultiTenantCompanyCreateMutation(MultiTenantCompanyPartialInput, extensions=extensions)


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
    login: MultiTenantUserType = auth.login()
    logout = auth.logout()

    # register_user: MultiTenantUserType = auth.register()
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
