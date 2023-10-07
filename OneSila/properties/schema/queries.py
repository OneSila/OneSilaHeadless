from core.schema.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List


from .types.types import PropertyType, PropertyTranslationType, \
    PropertySelectValueType, ProductPropertyType


@type(name="Query")
class PropertiesQuery:
    property_type: PropertyType = node()
    property_types: ListConnectionWithTotalCount[PropertyType] = connection()

    property_translation: PropertyTranslationType = node()
    property_translations: ListConnectionWithTotalCount[PropertyTranslationType] = connection()

    property_select_value: PropertySelectValueType = node()
    property_select_values: ListConnectionWithTotalCount[PropertySelectValueType] = connection()

    product_property_type: ProductPropertyType = node()
    product_property_types: ListConnectionWithTotalCount[ProductPropertyType] = connection()
