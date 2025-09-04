from strawberry_django.auth.utils import get_current_user

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
        ordering = queryset.model._meta.ordering
        return queryset.filter(multi_tenant_company=multi_tenant_company).order_by(*ordering)


class GetProductQuerysetMultiTenantMixin:
    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        multi_tenant_company = get_multi_tenant_company(info)
        queryset = queryset.filter(multi_tenant_company=multi_tenant_company)

        if hasattr(queryset, "with_translated_name"):
            queryset = queryset.with_translated_name(language_code=multi_tenant_company.language).order_by("translated_name")
        else:
            queryset = queryset.order_by(*queryset.model._meta.ordering)

        return queryset


class GetPropertyQuerysetMultiTenantMixin:
    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        multi_tenant_company = get_multi_tenant_company(info)
        queryset = queryset.filter(multi_tenant_company=multi_tenant_company)

        if hasattr(queryset, "with_translated_name"):
            queryset = queryset.with_translated_name(language_code=multi_tenant_company.language).order_by("translated_name")
        else:
            queryset = queryset.order_by(*queryset.model._meta.ordering)

        return queryset


class GetPropertySelectValueQuerysetMultiTenantMixin:
    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        multi_tenant_company = get_multi_tenant_company(info)
        queryset = queryset.filter(multi_tenant_company=multi_tenant_company)

        if hasattr(queryset, "with_translated_value"):
            queryset = queryset.with_translated_value(language_code=multi_tenant_company.language).order_by("translated_value")
        else:
            queryset = queryset.order_by(*queryset.model._meta.ordering)

        return queryset


class GetCurrentUserMixin:
    @classmethod
    def get_current_user(self, info, fail_silently=False):
        current_user = get_current_user(info)

        if not fail_silently and not current_user:
            raise ValueError("Unable to identify the current user.")

        return current_user
