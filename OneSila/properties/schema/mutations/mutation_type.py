from core.schema.core.mutations import type
from core.schema.core.mutations import create, update, delete, type, List
from .fields import create_property, create_property_select_value

from ..types.types import PropertyType, PropertyTranslationType, PropertySelectValueType, ProductPropertyType, ProductPropertyTextTranslationType, \
    PropertySelectValueTranslationType, ProductPropertiesRuleType, ProductPropertiesRuleItemType
from ..types.input import PropertyInput, PropertyTranslationInput, PropertySelectValueInput, ProductPropertyInput, \
    PropertyPartialInput, PropertyTranslationPartialInput, PropertySelectValuePartialInput, ProductPropertyPartialInput, ProductPropertyTextTranslationInput, \
    PropertySelectValueTranslationInput, PropertySelectValueTranslationPartialInput, ProductPropertyTextTranslationPartialInput, ProductPropertiesRuleInput, \
    ProductPropertiesRulePartialInput, ProductPropertiesRuleItemInput, ProductPropertiesRuleItemPartialInput


@type(name="Mutation")
class PropertiesMutation:
    create_property: PropertyType = create_property()
    create_properties: List[PropertyType] = create(PropertyInput)
    update_property: PropertyType = update(PropertyPartialInput)
    delete_property: PropertyType = delete()
    delete_properties: List[PropertyType] = delete()

    create_property_translation: PropertyTranslationType = create(PropertyTranslationInput)
    create_property_translations: List[PropertyTranslationType] = create(PropertyTranslationInput)
    update_property_translation: PropertyTranslationType = update(PropertyTranslationPartialInput)
    delete_property_translation: PropertyTranslationType = delete()
    delete_property_translations: List[PropertyTranslationType] = delete()

    create_property_select_value: PropertySelectValueType = create_property_select_value()
    create_property_select_values: List[PropertySelectValueType] = create(PropertySelectValueInput)
    update_property_select_value: PropertySelectValueType = update(PropertySelectValuePartialInput)
    delete_property_select_value: PropertySelectValueType = delete()
    delete_property_select_values: List[PropertySelectValueType] = delete()

    create_product_property: ProductPropertyType = create(ProductPropertyInput)
    create_product_properties: List[ProductPropertyType] = create(ProductPropertyInput)
    update_product_property: ProductPropertyType = update(ProductPropertyPartialInput)
    delete_product_property: ProductPropertyType = delete()
    delete_product_properties: List[ProductPropertyType] = delete()

    create_product_property_text_translation: ProductPropertyTextTranslationType = create(ProductPropertyTextTranslationInput)
    create_product_property_text_translations: List[ProductPropertyTextTranslationType] = create(ProductPropertyTextTranslationInput)
    update_product_property_text_translation: ProductPropertyTextTranslationType = update(ProductPropertyTextTranslationPartialInput)
    delete_product_property_text_translation: ProductPropertyTextTranslationType = delete()
    delete_product_property_text_translations: List[ProductPropertyTextTranslationType] = delete()

    create_property_select_value_translation: PropertySelectValueTranslationType = create(PropertySelectValueTranslationInput)
    create_property_select_value_translations: List[PropertySelectValueTranslationType] = create(PropertySelectValueTranslationInput)
    update_property_select_value_translation: PropertySelectValueTranslationType = update(PropertySelectValueTranslationPartialInput)
    delete_property_select_value_translation: PropertySelectValueTranslationType = delete()
    delete_property_select_value_translations: List[PropertySelectValueTranslationType] = delete()

    create_product_properties_rule: ProductPropertiesRuleType = create(ProductPropertiesRuleInput)
    create_product_properties_rules: List[ProductPropertiesRuleType] = create(ProductPropertiesRuleInput)
    update_product_properties_rule: ProductPropertiesRuleType = update(ProductPropertiesRulePartialInput)
    delete_product_properties_rule: ProductPropertiesRuleType = delete()
    delete_product_properties_rules: List[ProductPropertiesRuleType] = delete()

    create_product_properties_rule_item: ProductPropertiesRuleItemType = create(ProductPropertiesRuleItemInput)
    create_product_properties_rule_items: List[ProductPropertiesRuleItemType] = create(ProductPropertiesRuleItemInput)
    update_product_properties_rule_item: ProductPropertiesRuleItemType = update(ProductPropertiesRuleItemPartialInput)
    delete_product_properties_rule_item: ProductPropertiesRuleItemType = delete()
    delete_product_properties_rule_items: List[ProductPropertiesRuleItemType] = delete()
