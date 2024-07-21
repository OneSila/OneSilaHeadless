from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List


from .types.types import PropertyType, PropertyTranslationType, \
    PropertySelectValueType, ProductPropertyType, ProductPropertyTextTranslationType, PropertySelectValueTranslationType


@type(name="Query")
class PropertiesQuery:
    property: PropertyType = node()
    properties: ListConnectionWithTotalCount[PropertyType] = connection()

    property_translation: PropertyTranslationType = node()
    property_translations: ListConnectionWithTotalCount[PropertyTranslationType] = connection()

    property_select_value: PropertySelectValueType = node()
    property_select_values: ListConnectionWithTotalCount[PropertySelectValueType] = connection()

    product_property: ProductPropertyType = node()
    product_properties: ListConnectionWithTotalCount[ProductPropertyType] = connection()

    product_property_text_translation: ProductPropertyTextTranslationType = node()
    product_property_text_translations: ListConnectionWithTotalCount[ProductPropertyTextTranslationType] = connection()

    property_select_value_translation: PropertySelectValueTranslationType = node()
    property_select_value_translations: ListConnectionWithTotalCount[PropertySelectValueTranslationType] = connection()

