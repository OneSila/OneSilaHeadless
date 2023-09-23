from core.schema.types.types import auto
from core.schema.types.filters import filter

from properties.models import Property, ProductProperty
from product.schema.types.filters import ProductFilter


@filter(Property)
class PropertyFilter:
    id: auto
    type: auto


@filter(PropertySelectValue)
class PropertySelectValueFilter:
    id: auto
    property: PropertyFilter
    value: auto


@filter(ProductProperty)
class ProductPropertyFilter:
    id: auto
    product: ProductFilter
    property: PropertyFilter
    value: auto
    value_select: PropertySelectValueFilter
    value_multi_select: PropertySelectValueFilter
