from strawberry.types import Info
from strawberry_django.auth.queries import get_current_user


class GetMultiTenantCompanyMixin:
    @staticmethod
    def get_multi_tenant_company(info: Info):
        user = get_current_user(info)
        return user.multi_tenant_company


class GetQuerysetMultiTenantMixin:
    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        multi_tenant_company = GetMultiTenantCompanyMixin.get_multi_tenant_company(info)
        return queryset.filter(multi_tenant_company=multi_tenant_company)
