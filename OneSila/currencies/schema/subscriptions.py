from core.schema.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from currencies.models import Currency
from currencies.schema.types.types import CurrencyType


@type(name="Subscription")
class CurrenciesSubscription:
    # company: AsyncGenerator[CompanyType, None] = model_subscription_field(Company)

    @subscription
    async def currency(self, info: Info, pk: str) -> AsyncGenerator[CurrencyType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Currency):
            yield i
