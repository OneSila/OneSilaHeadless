from strawberry_django import auth

from core.schema.mutations import create, type, DjangoUpdateMutation, \
    GetMultiTenantCompanyMixin, default_extensions, update, Info, models, \
    Iterable, Any
from core.schema.mixins import GetQuerysetMultiTenantMixin

from .types.types import MultiTenantUserType, MultiTenantCompanyType
from .types.input import MultiTenantUserInput, MultiTenantUserPartialInput, \
    MultiTenantCompanyPartialInput, MultiTenantCompanyInput


class MultiTentantCompanyUpdateMutation(GetMultiTenantCompanyMixin, DjangoUpdateMutation):
    """
    This mutation will only protect against having a multi-tentant company.
    Not the existance on the model, since the MultiTenantCompany has no reference to itself.
    """

    def update(self, info: Info, instance: models.Model | Iterable[models.Model], data: dict[str, Any],):
        return super().update(info=info, instance=instance, data=data)


def update_multi_company(input_type):
    extensions = default_extensions
    return MultiTentantCompanyUpdateMutation(input_type, extensions=extensions)


@type(name="Mutation")
class MultiTenantMutation:
    login: MultiTenantUserType = auth.login()
    logout = auth.logout()
    register_user: MultiTenantUserType = auth.register(MultiTenantUserInput)
    register_multi_tenant_company: MultiTenantCompanyType = create(MultiTenantUserInput)

    # FIXME: You should only be able to update yourself. Not other users. (unless it's to disable)
    update_user: MultiTenantUserType = update(MultiTenantUserPartialInput)

    # FIXME: You should only be able to update your own multi tenant company. Not other users. (unless it's to disable)
    update_multi_tenant_company: MultiTenantCompanyType = update_multi_company(MultiTenantCompanyPartialInput)
