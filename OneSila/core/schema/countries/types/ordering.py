from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from core.models.multi_tenant import MultiTenantUser


@order(MultiTenantUser)
class MultiTenantUserOrder:
    username: auto
    last_name: auto
    first_name: auto
