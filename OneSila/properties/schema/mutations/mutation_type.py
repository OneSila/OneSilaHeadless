from core.schema.core.mutations import create, update, delete, type, List
from typing import List as TypingList
from strawberry import Info
import strawberry_django
from core.schema.core.extensions import default_extensions
from core.schema.core.helpers import get_multi_tenant_company, get_current_user
from .fields import complete_create_product_properties_rule, complete_update_product_properties_rule, \
    bulk_create_product_properties, create_property, create_property_select_value
from ..types.types import PropertyType, PropertyTranslationType, PropertySelectValueType, ProductPropertyType, ProductPropertyTextTranslationType, \
    PropertySelectValueTranslationType, ProductPropertiesRuleType, ProductPropertiesRuleItemType, PropertyDuplicatesType, PropertySelectValueDuplicatesType
from properties.models import Property, PropertySelectValue, ProductProperty, ProductPropertyTextTranslation
from ..types.input import PropertyInput, PropertyTranslationInput, PropertySelectValueInput, ProductPropertyInput, \
    PropertyPartialInput, PropertyTranslationPartialInput, PropertySelectValuePartialInput, ProductPropertyPartialInput, ProductPropertyTextTranslationInput, \
    PropertySelectValueTranslationInput, PropertySelectValueTranslationPartialInput, ProductPropertyTextTranslationPartialInput, ProductPropertiesRuleInput, \
    ProductPropertiesRulePartialInput, ProductPropertiesRuleItemInput, ProductPropertiesRuleItemPartialInput, BulkProductPropertyPartialInput
from strawberry_django.mutations.types import UNSET


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

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def bulk_update_product_properties(
        self,
        info: Info,
        product_properties: TypingList[BulkProductPropertyPartialInput],
    ) -> TypingList[ProductPropertyType]:
        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        multi_tenant_user = get_current_user(info)
        updated: list[ProductProperty] = []
        for item in product_properties:
            item_data = vars(item).copy()
            obj_id = item_data.pop("id").node_id
            translation_data = item_data.pop("translation", None)
            value_multi_select = item_data.pop("value_multi_select", UNSET)
            value_select = item_data.pop("value_select", UNSET)
            obj = ProductProperty.objects.get(id=obj_id)
            if obj.multi_tenant_company != multi_tenant_company:
                raise PermissionError("Invalid company")
            for field, value in item_data.items():
                if value is not UNSET:
                    setattr(obj, field, value)
            obj.last_update_by_multi_tenant_user = multi_tenant_user
            obj.save()
            if value_select is not UNSET:
                if value_select is None:
                    obj.value_select = None
                else:
                    obj.value_select_id = value_select.id.node_id
                obj.save()
            if value_multi_select is not UNSET:
                values: list[int] = []
                if value_multi_select is not None:
                    values = [v.id.node_id for v in value_multi_select]
                obj.value_multi_select.set(values)
            if translation_data:
                language_code = translation_data.language_code
                try:
                    translation = ProductPropertyTextTranslation.objects.get(
                        product_property=obj,
                        language=language_code,
                    )
                    translation.last_update_by_multi_tenant_user = multi_tenant_user
                except ProductPropertyTextTranslation.DoesNotExist:
                    translation = ProductPropertyTextTranslation(
                        product_property=obj,
                        language=language_code,
                        multi_tenant_company=multi_tenant_company,
                        created_by_multi_tenant_user=multi_tenant_user,
                        last_update_by_multi_tenant_user=multi_tenant_user,
                    )
                if translation_data.value_text is not None:
                    translation.value_text = translation_data.value_text
                if translation_data.value_description is not None:
                    translation.value_description = translation_data.value_description
                translation.save()
            updated.append(obj)
        return updated

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
        property_instance = Property.objects.get(id=property.id.node_id)
        duplicates = PropertySelectValue.objects.check_for_duplicates(
            value,
            property_instance,
            multi_tenant_company,
        )
        return PropertySelectValueDuplicatesType(
            duplicate_found=duplicates.exists(),
            duplicates=list(duplicates),
        )
