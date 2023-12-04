from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber
from core.schema.core.subscriptions.helpers import create_global_id
from core.schema.core.helpers import get_multi_tenant_company, get_current_user
from core.schema.multi_tenant.types.types import MultiTenantUserType, MultiTenantCompanyType
from core.models.multi_tenant import MultiTenantUser, MultiTenantCompany

from asgiref.sync import sync_to_async


@type(name="Subscription")
class MultiTenantSubscription:
    @subscription
    async def me(self, info: Info) -> AsyncGenerator[MultiTenantUserType, None]:
        user = get_current_user(info)
        pk = create_global_id(user)
        async for i in model_subscriber(info=info, pk=pk, model=MultiTenantUser, multi_tenant_company_protection=False):
            yield i

    @subscription
    async def my_multi_tenant_company(self, info: Info) -> AsyncGenerator[MultiTenantCompanyType, None]:
        multi_tenant_company = await sync_to_async(get_multi_tenant_company)(info)
        pk = create_global_id(multi_tenant_company)
        async for i in model_subscriber(info=info, pk=pk, model=MultiTenantCompany, multi_tenant_company_protection=False):
            yield i
