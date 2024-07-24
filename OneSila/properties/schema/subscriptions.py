from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from properties.models import Property, PropertyTranslation, PropertySelectValue, ProductProperty, ProductPropertyTextTranslation, \
    PropertySelectValueTranslation, ProductPropertiesRule, ProductPropertiesRuleItem
from properties.schema.types.types import PropertyType, PropertyTranslationType, \
    PropertySelectValueType, ProductPropertyType, ProductPropertyTextTranslationType, PropertySelectValueTranslationType, ProductPropertiesRuleType, \
    ProductPropertiesRuleItemType


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
    async def property_select_value(self, info: Info, pk: str) -> AsyncGenerator[PropertySelectValueType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=PropertySelectValue):
            yield i

    @subscription
    async def product_property(self, info: Info, pk: str) -> AsyncGenerator[ProductPropertyType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=ProductProperty):
            yield i

    @subscription
    async def product_property_text_translation(self, info: Info, pk: str) -> AsyncGenerator[ProductPropertyTextTranslationType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=ProductPropertyTextTranslation):
            yield i

    @subscription
    async def property_select_value_translation(self, info: Info, pk: str) -> AsyncGenerator[PropertySelectValueTranslationType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=PropertySelectValueTranslation):
            yield i

    @subscription
    async def product_properties_rule(self, info: Info, pk: str) -> AsyncGenerator[ProductPropertiesRuleType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=ProductPropertiesRule):
            yield i

    @subscription
    async def product_properties_rule_item(self, info: Info, pk: str) -> AsyncGenerator[ProductPropertiesRuleItemType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=ProductPropertiesRuleItem):
            yield i