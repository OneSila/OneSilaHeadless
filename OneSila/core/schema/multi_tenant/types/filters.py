from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter
from core.models.multi_tenant import MultiTenantCompany, MultiTenantUser


@filter(MultiTenantUser)
class MultiTenantUserFilter:
    first_name: auto
    last_name: auto
    username: auto
    is_active: auto
    invitation_accepted: auto
    is_multi_tenant_company_owner: auto
