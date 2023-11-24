from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin

from typing import List

from properties.models import Property, PropertyTranslation, \
    PropertySelectValue, ProductProperty
from .filters import PropertyFilter, PropertyTranslationFilter, \
    PropertySelectValueFilter, ProductPropertyFilter
from .ordering import PropertyOrder, PropertyTranslationOrder, \
    PropertySelectValueOrder, ProductPropertyOrder


@type(Property, filters=PropertyFilter, order=PropertyOrder, pagination=True, fields="__all__")
class PropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(PropertyTranslation, filters=PropertyTranslationFilter, order=PropertyTranslationOrder, pagination=True, fields="__all__")
class PropertyTranslationType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(PropertySelectValue, filters=PropertySelectValueFilter, order=PropertySelectValueOrder, pagination=True, fields="__all__")
class PropertySelectValueType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(ProductProperty, filters=ProductPropertyFilter, order=ProductPropertyOrder, pagination=True, fields="__all__")
class ProductPropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
