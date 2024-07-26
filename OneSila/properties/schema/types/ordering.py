from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from properties.models import Property, PropertySelectValue, \
    ProductProperty, PropertyTranslation, ProductPropertyTextTranslation, PropertySelectValueTranslation, ProductPropertiesRuleItem, ProductPropertiesRule


@order(Property)
class PropertyOrder:
    id: auto
    type: auto


@order(PropertySelectValue)
class PropertySelectValueOrder:
    id: auto


@order(PropertySelectValueTranslation)
class PropertySelectValueTranslationOrder:
    id: auto
    value: auto

@order(ProductProperty)
class ProductPropertyOrder:
    id: auto
    value_select: auto
    value_multi_select: auto


@order(PropertyTranslation)
class PropertyTranslationOrder:
    id: auto

@order(ProductPropertyTextTranslation)
class ProductPropertyTextTranslationOrder:
    id: auto

@order(ProductPropertiesRule)
class ProductPropertiesRuleOrder:
    id: auto
    product_type: auto

@order(ProductPropertiesRuleItem)
class ProductPropertiesRuleItemOrder:
    sort_order: auto