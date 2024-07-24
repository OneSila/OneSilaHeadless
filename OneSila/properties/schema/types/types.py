from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field, Annotated, lazy

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
class PropertyType(relay.Node, GetQuerysetMultiTenantMixin):

    @field()
    def name(self, info) -> str | None:
        return self.name


@type(PropertyTranslation, filters=PropertyTranslationFilter, order=PropertyTranslationOrder, pagination=True, fields="__all__")
class PropertyTranslationType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(PropertySelectValue, filters=PropertySelectValueFilter, order=PropertySelectValueOrder, pagination=True, fields="__all__")
class PropertySelectValueType(relay.Node, GetQuerysetMultiTenantMixin):
    property: PropertyType
    image: Optional[ImageType]

    @field()
    def value(self, info) -> str | None:
        return self.value


@type(PropertySelectValueTranslation, filters=PropertySelectValueTranslationFilter, order=PropertySelectValueTranslationOrder, pagination=True,
      fields="__all__")
class PropertySelectValueTranslationType(relay.Node, GetQuerysetMultiTenantMixin):
    propertyselectvalue: PropertySelectValueType


@type(ProductProperty, filters=ProductPropertyFilter, order=ProductPropertyOrder, pagination=True, fields="__all__")
class ProductPropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(ProductPropertyTextTranslation, filters=ProductPropertyTextTranslationFilter, order=ProductPropertyTextTranslationOrder, pagination=True,
      fields="__all__")
class ProductPropertyTextTranslationType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(ProductPropertiesRule, filters=ProductPropertiesRuleFilter, order=ProductPropertiesRuleOrder, pagination=True, fields="__all__")
class ProductPropertiesRuleType(relay.Node):
    product_type: PropertySelectValueType
    items: List[Annotated['ProductPropertiesRuleItemType', lazy("properties.schema.types.types")]]


@type(ProductPropertiesRuleItem, filters=ProductPropertiesRuleItemFilter, order=ProductPropertiesRuleItemOrder, pagination=True, fields="__all__")
class ProductPropertiesRuleItemType(relay.Node):
    rule: ProductPropertiesRuleType
    property: PropertyType
