from .publishers import ModelInstanceSubscribePublisher
from .typing import GlobalID, Info, Model, AsyncGenerator, Any

from strawberry import subscription


async def model_subscriber(info: Info, pk: GlobalID, model: Model, multi_tenant_company_protection: bool = True) -> AsyncGenerator[Any, None]:
    publisher = ModelInstanceSubscribePublisher(info=info, pk=pk, model=model, multi_tenant_company_protection=multi_tenant_company_protection)
    async for msg in publisher.await_messages():
        yield msg


def model_subscription_field(model):
    # FIXME: Using this wrapper with @subscription breaks somewhere inside of the subscription decorator.
    # using it without @subscription return None instead of the AsyncGenerator.
    @subscription
    async def model_subscription_inner(info: Info, pk: GlobalID, model: Model) -> AsyncGenerator[Any, None]:
        async for i in model_subscriber(info=info, pk=pk, model=model):
            yield i
    return model_subscription_inner
