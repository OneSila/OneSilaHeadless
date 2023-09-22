from strawberry.types import Info
from django_shared_multi_tenant.schema import StrawberryMultitenantMixin


class GetMultiTenantCompanyMixin:
    def get_multi_tenant_company(self, info: Info):
        return info.context.request.user.multi_tenant_company


class TypeMultiTenantFilterMixin(StrawberryMultitenantMixin):
    pass
