from core.schema.core.mutations import create, update, delete, type, List
from strawberry import Info
import strawberry_django
from core.schema.core.extensions import default_extensions
from core.schema.core.helpers import get_multi_tenant_company
from .fields import complete_create_product_properties_rule, complete_update_product_properties_rule, \
    bulk_create_product_properties, create_property, create_property_select_value
from ..types.types import PropertyType, PropertyTranslationType, PropertySelectValueType, ProductPropertyType, ProductPropertyTextTranslationType, \
    PropertySelectValueTranslationType, ProductPropertiesRuleType, ProductPropertiesRuleItemType, PropertyDuplicatesType, PropertySelectValueDuplicatesType
from properties.models import Property, PropertySelectValue
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
    delete_properties: List[PropertyType] = delete(is_bulk=True)

    create_property_translation: PropertyTranslationType = create(PropertyTranslationInput)
    create_property_translations: List[PropertyTranslationType] = create(PropertyTranslationInput)
    update_property_translation: PropertyTranslationType = update(PropertyTranslationPartialInput)
    delete_property_translation: PropertyTranslationType = delete()
    delete_property_translations: List[PropertyTranslationType] = delete()

    create_property_select_value: PropertySelectValueType = create_property_select_value()
    create_property_select_values: List[PropertySelectValueType] = create(PropertySelectValueInput)
    update_property_select_value: PropertySelectValueType = update(PropertySelectValuePartialInput)
    delete_property_select_value: PropertySelectValueType = delete()
    delete_property_select_values: List[PropertySelectValueType] = delete(is_bulk=True)

    create_product_property: ProductPropertyType = create(ProductPropertyInput)
    create_product_properties: List[ProductPropertyType] = create(ProductPropertyInput)
    bulk_create_product_properties: List[ProductPropertyType] = bulk_create_product_properties()
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
    complete_create_product_properties_rule: ProductPropertiesRuleType = complete_create_product_properties_rule()
    create_product_properties_rules: List[ProductPropertiesRuleType] = create(ProductPropertiesRuleInput)
    update_product_properties_rule: ProductPropertiesRuleType = update(ProductPropertiesRulePartialInput)
    complete_update_product_properties_rule: ProductPropertiesRuleType = complete_update_product_properties_rule()
    delete_product_properties_rule: ProductPropertiesRuleType = delete()
    delete_product_properties_rules: List[ProductPropertiesRuleType] = delete(is_bulk=True)

    create_product_properties_rule_item: ProductPropertiesRuleItemType = create(ProductPropertiesRuleItemInput)
    create_product_properties_rule_items: List[ProductPropertiesRuleItemType] = create(ProductPropertiesRuleItemInput)
    update_product_properties_rule_item: ProductPropertiesRuleItemType = update(ProductPropertiesRuleItemPartialInput)
    delete_product_properties_rule_item: ProductPropertiesRuleItemType = delete()
    delete_product_properties_rule_items: List[ProductPropertiesRuleItemType] = delete()

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def check_property_for_duplicates(self, name: str, info: Info) -> PropertyDuplicatesType:
        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        duplicates = Property.objects.check_for_duplicates(name, multi_tenant_company)
        return PropertyDuplicatesType(
            duplicate_found=duplicates.exists(),
            duplicates=list(duplicates),
        )

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def check_property_select_value_for_duplicates(
        self,
        value: str,
        property: PropertyPartialInput,
        info: Info,
    ) -> PropertySelectValueDuplicatesType:
        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        property_instance = property.pk
        duplicates = PropertySelectValue.objects.check_for_duplicates(
            value,
            property_instance,
            multi_tenant_company,
        )
        return PropertySelectValueDuplicatesType(
            duplicate_found=duplicates.exists(),
            duplicates=list(duplicates),
        )
