from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from core.models.multi_tenant import MultiTenantUser, DashboardSection, DashboardCard


@order(MultiTenantUser)
class MultiTenantUserOrder:
    username: auto
    last_name: auto
    first_name: auto


@order(DashboardSection)
class DashboardSectionOrder:
    id: auto
    title: auto
    sort_order: auto
    created_at: auto
    updated_at: auto


@order(DashboardCard)
class DashboardCardOrder:
    id: auto
    title: auto
    sort_order: auto
    query_key: auto
    created_at: auto
    updated_at: auto
