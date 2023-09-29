from core.schema.subscriptions import type, subscription, Info, AsyncGenerator, asyncio, node, field, List

from contacts.models import Company
from .types.input import CompanyPartialInput
from .types.types import CompanyType

import json


@type(name="Subscription")
class ContactsSubscription:
    company: CompanyType = node(is_subscription=True)
    companies: List[CompanyType] = field(is_subscription=True)

    @subscription
    async def count(self, target: int = 100) -> int:
        for i in range(target):
            yield i
            await asyncio.sleep(0.5)
