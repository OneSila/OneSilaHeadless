from .helpers import get_multi_tenant_company


class GetMultiTenantCompanyMixin:
    def get_multi_tenant_company(self, info, fail_silently=False):
        multi_tenant_company = get_multi_tenant_company(info)

        if not fail_silently and not multi_tenant_company:
            raise ValueError("Missing value for multi_tenant_company in create values")

        return multi_tenant_company


class GetQuerysetMultiTenantMixin:
    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        multi_tenant_company = get_multi_tenant_company(info)
        return queryset.filter(multi_tenant_company=multi_tenant_company)
