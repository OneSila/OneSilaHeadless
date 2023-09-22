from strawberry.types import Info


class GetMultiTenantCompanyMixin:
    def get_multi_tenant_company(self, info: Info):
        return info.context.request.user.multi_tenant_company


class GetQuerysetMultiTenantMixin:
    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return queryset.filter(multi_tenant_company=info.context.request.user.multi_tenant_company)
