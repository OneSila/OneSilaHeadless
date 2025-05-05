from core.schema.core.queries import node, connection, DjangoListConnection, type
from typing import List


from .types.types import PropertyType, PropertyTranslationType, \
    PropertySelectValueType, ProductPropertyType, ProductPropertyTextTranslationType, PropertySelectValueTranslationType, ProductPropertiesRuleType, \
    ProductPropertiesRuleItemType


@type(name="Query")
class PropertiesQuery:
    property: PropertyType = node()
    properties: DjangoListConnection[PropertyType] = connection()

    property_translation: PropertyTranslationType = node()
    property_translations: DjangoListConnection[PropertyTranslationType] = connection()

    property_select_value: PropertySelectValueType = node()
    property_select_values: DjangoListConnection[PropertySelectValueType] = connection()

    product_property: ProductPropertyType = node()
    product_properties: DjangoListConnection[ProductPropertyType] = connection()

    product_property_text_translation: ProductPropertyTextTranslationType = node()
    product_property_text_translations: DjangoListConnection[ProductPropertyTextTranslationType] = connection()

    property_select_value_translation: PropertySelectValueTranslationType = node()
    property_select_value_translations: DjangoListConnection[PropertySelectValueTranslationType] = connection()

    product_properties_rule: ProductPropertiesRuleType = node()
    product_properties_rules: DjangoListConnection[ProductPropertiesRuleType] = connection()

    product_properties_rule_item: ProductPropertiesRuleItemType = node()
    product_properties_rule_items: DjangoListConnection[ProductPropertiesRuleItemType] = connection()
