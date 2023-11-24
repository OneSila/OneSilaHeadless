from strawberry_django import auth
from strawberry_django.resolvers import django_resolver
from strawberry_django.mutations import resolvers
from strawberry_django.auth.utils import get_current_user

from django.db import transaction

from core.schema.core.mutations import create, type, DjangoUpdateMutation, \
    GetMultiTenantCompanyMixin, default_extensions, update, Info, models, \
    Iterable, Any
from core.schema.core.mixins import GetQuerysetMultiTenantMixin

from .types.types import MultiTenantUserType, MultiTenantCompanyType
from .types.input import MultiTenantUserInput, MultiTenantUserPartialInput, \
    MultiTenantCompanyPartialInput, MultiTenantCompanyInput


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


def update_my_multi_tenant_company(input_type):
    extensions = default_extensions
    return MyMultiTentantCompanyUpdateMutation(input_type, extensions=extensions)


def update_me(input_type):
    extensions = default_extensions
    return UpdateMeMutation(input_type, extensions=extensions)


@type(name="Mutation")
class MultiTenantMutation:
    login: MultiTenantUserType = auth.login()
    logout = auth.logout()

    register_user: MultiTenantUserType = auth.register(MultiTenantUserInput)
    register_multi_tenant_company: MultiTenantCompanyType = create(MultiTenantUserInput)

    update_me: MultiTenantUserType = update_me(MultiTenantUserPartialInput)
    update_my_multi_tenant_company: MultiTenantCompanyType = update_my_multi_tenant_company(MultiTenantCompanyPartialInput)

    # TODO: Invite user mutation.
    # this mutation will:
    # create "un-activated" user
    # assign to multi-tenant-company
    # send out email to invite and resturn invitation link
    # + query/mutation flow for the user to actually subscribe.
    # + mutation to re-invite the user
