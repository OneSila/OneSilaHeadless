from core.schema.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from properties.models import Property, PropertyTranslation, PropertySelectValue, ProductProperty
from properties.schema.types.types import PropertyType, PropertyTranslationType, \
    PropertySelectValueType, ProductPropertyType


@type(name="Subscription")
class PropertiesSubscription:
    @subscription
    async def property(self, info: Info, pk: str) -> AsyncGenerator[PropertyTranslationType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Property):
            yield i

    @subscription
    async def property_translation(self, info: Info, pk: str) -> AsyncGenerator[PropertyTranslationType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=PropertyTranslation):
            yield i

    @subscription
    async def propertyselect_value(self, info: Info, pk: str) -> AsyncGenerator[PropertySelectValueType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=PropertySelectValue):
            yield i

    @subscription
    async def product_property(self, info: Info, pk: str) -> AsyncGenerator[ProductPropertyType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=ProductProperty):
            yield i
