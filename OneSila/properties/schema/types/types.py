from core.schema.core.types.types import relay, type, field, Annotated, lazy
import strawberry
from core.schema.core.mixins import (
    GetPropertyQuerysetMultiTenantMixin,
    GetPropertySelectValueQuerysetMultiTenantMixin,
    GetQuerysetMultiTenantMixin,
)

from typing import List, Optional
from media.schema.types.types import ImageType
from properties.models import Property, PropertyTranslation, \
    PropertySelectValue, ProductProperty, ProductPropertyTextTranslation, PropertySelectValueTranslation, ProductPropertiesRule, ProductPropertiesRuleItem
from .filters import PropertyFilter, PropertyTranslationFilter, \
    PropertySelectValueFilter, ProductPropertyFilter, ProductPropertyTextTranslationFilter, PropertySelectValueTranslationFilter, ProductPropertiesRuleFilter, \
    ProductPropertiesRuleItemFilter
from .ordering import PropertyOrder, PropertyTranslationOrder, \
    PropertySelectValueOrder, ProductPropertyOrder, ProductPropertyTextTranslationOrder, PropertySelectValueTranslationOrder, ProductPropertiesRuleOrder, \
    ProductPropertiesRuleItemOrder


@type(Property, filters=PropertyFilter, order=PropertyOrder, pagination=True, fields="__all__")
class PropertyType(relay.Node, GetPropertyQuerysetMultiTenantMixin):
    propertytranslation_set: List[Annotated['PropertyTranslationType', lazy("properties.schema.types.types")]]

    @field()
    def name(self, info) -> str | None:
        return self.name


@type(PropertyTranslation, filters=PropertyTranslationFilter, order=PropertyTranslationOrder, pagination=True, fields="__all__")
class PropertyTranslationType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(PropertySelectValue, filters=PropertySelectValueFilter, order=PropertySelectValueOrder, pagination=True, fields="__all__")
class PropertySelectValueType(relay.Node, GetPropertySelectValueQuerysetMultiTenantMixin):
    property: PropertyType
    image: Optional[ImageType]
    productpropertiesrule_set: List[Annotated['ProductPropertiesRuleType', lazy("properties.schema.types.types")]]
    propertyselectvaluetranslation_set: List[Annotated['PropertySelectValueTranslationType', lazy("properties.schema.types.types")]]

    @field()
    def value(self, info) -> str | None:
        return self.value

    @field()
    def full_value_name(self, info) -> str | None:
        return f"{self.property.name} > {self.value}"

    @field()
    def thumbnail_url(self, info) -> str | None:
        if self.image:
            return self.image.image_web_url

        return None


@type(PropertySelectValueTranslation, filters=PropertySelectValueTranslationFilter, order=PropertySelectValueTranslationOrder, pagination=True,
      fields="__all__")
class PropertySelectValueTranslationType(relay.Node, GetQuerysetMultiTenantMixin):
    propertyselectvalue: PropertySelectValueType


@type(ProductProperty, filters=ProductPropertyFilter, order=ProductPropertyOrder, pagination=True, fields="__all__")
class ProductPropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    product: Optional[Annotated['ProductType', lazy("products.schema.types.types")]]
    property: Optional[PropertyType]
    value_select: Optional[PropertySelectValueType]
    value_multi_select: List[Annotated['PropertySelectValueType', lazy("properties.schema.types.types")]]


@type(ProductPropertyTextTranslation, filters=ProductPropertyTextTranslationFilter, order=ProductPropertyTextTranslationOrder, pagination=True,
      fields="__all__")
class ProductPropertyTextTranslationType(relay.Node, GetQuerysetMultiTenantMixin):
    product_property: ProductPropertyType


@type(ProductPropertiesRule, filters=ProductPropertiesRuleFilter, order=ProductPropertiesRuleOrder, pagination=True, fields="__all__")
class ProductPropertiesRuleType(relay.Node, GetQuerysetMultiTenantMixin):
    product_type: PropertySelectValueType
    items: List[Annotated['ProductPropertiesRuleItemType', lazy("properties.schema.types.types")]]

    @field()
    def value(self, info) -> str:
        return self.value


@type(ProductPropertiesRuleItem, filters=ProductPropertiesRuleItemFilter, order=ProductPropertiesRuleItemOrder, pagination=True, fields="__all__")
class ProductPropertiesRuleItemType(relay.Node, GetQuerysetMultiTenantMixin):
    rule: ProductPropertiesRuleType
    property: PropertyType


@strawberry.type
class PropertyDuplicatesType:
    duplicate_found: bool
    duplicates: List[PropertyType]
