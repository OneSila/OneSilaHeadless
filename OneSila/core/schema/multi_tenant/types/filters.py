from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, lazy
from core.models.multi_tenant import (
    MultiTenantCompany,
    MultiTenantUser,
    DashboardSection,
    DashboardCard,
)
from core.schema.core.helpers import get_current_user
from core.managers import QuerySet
from django.db.models import Q
from strawberry import UNSET
from strawberry_django import filter_field as custom_filter


@filter(MultiTenantUser)
class MultiTenantUserFilter:
    first_name: auto
    last_name: auto
    username: auto
    is_active: auto
    invitation_accepted: auto
    is_multi_tenant_company_owner: auto


@filter(DashboardSection, lookups=True)
class DashboardSectionFilter:
    title: auto
    description: auto
    user: Optional[lazy['MultiTenantUserFilter', "core.schema.multi_tenant.types.filters"]]
    current_user: Optional[bool]

    @custom_filter
    def current_user(
        self,
        queryset: QuerySet,
        info,
        value: bool,
        prefix: str,
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        user = get_current_user(info)
        if user is None:
            return queryset.none(), Q()

        if value:
            queryset = queryset.filter(user=user)

        return queryset, Q()


@filter(DashboardCard, lookups=True)
class DashboardCardFilter:
    title: auto
    color: auto
    query_key: auto
    section: Optional[lazy['DashboardSectionFilter', "core.schema.multi_tenant.types.filters"]]
    user: Optional[lazy['MultiTenantUserFilter', "core.schema.multi_tenant.types.filters"]]
    current_user: Optional[bool]

    @custom_filter
    def current_user(
        self,
        queryset: QuerySet,
        info,
        value: bool,
        prefix: str,
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        user = get_current_user(info)
        if user is None:
            return queryset.none(), Q()

        if value:
            queryset = queryset.filter(user=user)

        return queryset, Q()
