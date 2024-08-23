from typing import List, Optional
from strawberry.relay.types import GlobalID
import strawberry

from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial

from properties.models import Property, PropertyTranslation, \
    PropertySelectValue, ProductProperty, ProductPropertyTextTranslation, PropertySelectValueTranslation, ProductPropertiesRule, ProductPropertiesRuleItem


@input(Property, fields="__all__")
class PropertyInput:
    name: str


@partial(Property, fields="__all__")
class PropertyPartialInput(NodeInput):
    pass


@input(PropertyTranslation, fields="__all__")
class PropertyTranslationInput:
    pass


@partial(PropertyTranslation, fields="__all__")
class PropertyTranslationPartialInput(NodeInput):
    pass


@input(PropertySelectValue, fields="__all__")
class PropertySelectValueInput:
    value: str


@partial(PropertySelectValue, fields="__all__")
class PropertySelectValuePartialInput(NodeInput):
    pass


@input(PropertySelectValueTranslation, fields="__all__")
class PropertySelectValueTranslationInput:
    pass


@partial(PropertySelectValueTranslation, fields="__all__")
class PropertySelectValueTranslationPartialInput(NodeInput):
    pass


@input(ProductProperty, fields="__all__")
class ProductPropertyInput:
    value_multi_select: Optional[List[PropertySelectValuePartialInput]]


@partial(ProductProperty, fields="__all__")
class ProductPropertyPartialInput(NodeInput):
    value_multi_select: Optional[List[PropertySelectValuePartialInput]]


@input(ProductPropertyTextTranslation, fields="__all__")
class ProductPropertyTextTranslationInput:
    pass


@partial(ProductPropertyTextTranslation, fields="__all__")
class ProductPropertyTextTranslationPartialInput(NodeInput):
    pass


@input(ProductPropertiesRuleItem, fields="__all__")
class ProductPropertiesRuleItemInput:
    pass


@partial(ProductPropertiesRuleItem, fields="__all__")
class ProductPropertiesRuleItemPartialInput(NodeInput):
    pass


@strawberry.input
class CustomProductPropertiesRuleItemInput:
    id: GlobalID | None = None
    property: PropertyPartialInput
    type: str
    sort_order: Optional[int] = 0


@input(ProductPropertiesRule, fields="__all__")
class ProductPropertiesRuleInput:
    items: Optional[List[CustomProductPropertiesRuleItemInput]]


@partial(ProductPropertiesRule, fields="__all__")
class ProductPropertiesRulePartialInput(NodeInput):
    items: Optional[List[CustomProductPropertiesRuleItemInput]]
