from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter

from properties.models import Property, ProductProperty, \
    ProductProperty, PropertySelectValue, PropertyTranslation
from products.schema.types.filters import ProductFilter


@filter(Property)
class PropertyFilter:
    id: auto
    type: auto


@filter(PropertySelectValue)
class PropertySelectValueFilter:
    id: auto
    property: PropertyFilter
    # value: auto


@filter(ProductProperty)
class ProductPropertyFilter:
    id: auto
    product: ProductFilter
    property: PropertyFilter
    value_boolean: auto
    value_int: auto
    value_string: auto
    value_text: auto
    value_date: auto
    value_datetime: auto
    value_select: PropertySelectValueFilter
    value_multi_select: PropertySelectValueFilter


@filter(PropertyTranslation)
class PropertyTranslationFilter:
    id: auto
