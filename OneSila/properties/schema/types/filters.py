from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from properties.models import Property, ProductProperty, \
    ProductProperty, PropertySelectValue, PropertyTranslation, ProductPropertyTextTranslation, PropertySelectValueTranslation, ProductPropertiesRule, \
    ProductPropertiesRuleItem
from products.schema.types.filters import ProductFilter


@filter(Property)
class PropertyFilter(SearchFilterMixin):
    id: auto
    is_public_information: auto
    is_product_type: auto
    type: auto


@filter(PropertySelectValue)
class PropertySelectValueFilter(SearchFilterMixin):
    id: auto
    property: Optional[PropertyFilter]


@filter(PropertySelectValueTranslation)
class PropertySelectValueTranslationFilter:
    id: auto
    value: auto
    propertyselectvalue: Optional[PropertySelectValueFilter]


@filter(ProductProperty)
class ProductPropertyFilter(SearchFilterMixin):
    id: auto
    product: Optional[ProductFilter]
    property: Optional[PropertyFilter]
    value_boolean: auto
    value_int: auto
    value_date: auto
    value_datetime: auto
    value_select: Optional[PropertySelectValueFilter]
    value_multi_select: Optional[PropertySelectValueFilter]


@filter(PropertyTranslation)
class PropertyTranslationFilter:
    id: auto
    property: Optional[PropertyFilter]


@filter(ProductPropertyTextTranslation)
class ProductPropertyTextTranslationFilter:
    id: auto
    language: auto
    product_property: Optional[ProductPropertyFilter]


@filter(ProductPropertiesRule)
class ProductPropertiesRuleFilter:
    id: auto
    product_type: Optional[PropertyFilter]


@filter(ProductPropertiesRuleItem)
class ProductPropertiesRuleItemFilter:
    id: auto
    rule: Optional[ProductPropertiesRuleFilter]
    property: Optional[PropertyFilter]
    type: auto
