from core.schema.mutations import type
from core.schema.mutations import create, update, delete, type, List

from .types.types import PropertyType, PropertyTranslationType, PropertySelectValueType, ProductPropertyType
from .types.input import PropertyInput, PropertyTranslationInput, PropertySelectValueInput, ProductPropertyInput, \
    PropertyPartialInput, PropertyTranslationPartialInput, PropertySelectValuePartialInput, ProductPropertyPartialInput


@type(name="Mutation")
class PropertiesMutation:
    create_property: PropertyType = create(PropertyInput)
    create_properties: List[PropertyType] = create(PropertyInput)
    update_property: PropertyType = update(PropertyPartialInput)
    delete_property: PropertyType = delete()
    delete_properties: List[PropertyType] = delete()

    create_property_translation: PropertyTranslationType = create(PropertyTranslationInput)
    create_property_translations: List[PropertyTranslationType] = create(PropertyTranslationInput)
    update_property_translation: PropertyTranslationType = update(PropertyTranslationPartialInput)
    delete_property_translation: PropertyTranslationType = delete()
    delete_property_translations: List[PropertyTranslationType] = delete()

    create_property_select_value: PropertySelectValueType = create(PropertySelectValueInput)
    create_property_select_values: List[PropertySelectValueType] = create(PropertySelectValueInput)
    update_property_select_value: PropertySelectValueType = update(PropertySelectValuePartialInput)
    delete_property_select_value: PropertySelectValueType = delete()
    delete_property_select_values: List[PropertySelectValueType] = delete()

    create_product_property: ProductPropertyType = create(ProductPropertyInput)
    create_product_properties: List[ProductPropertyType] = create(ProductPropertyInput)
    update_product_property: ProductPropertyType = update(ProductPropertyPartialInput)
    delete_product_property: ProductPropertyType = delete()
    delete_product_properties: List[ProductPropertyType] = delete()
