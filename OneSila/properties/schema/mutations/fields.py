from typing import List

from properties.schema.mutations.mutation_classes import CompleteCreateProductPropertiesRule, \
    CompleteUpdateProductPropertiesRule, BulkCreateProductProperties
from properties.schema.types.input import PropertyInput, PropertySelectValueInput, ProductPropertiesRuleInput, \
    ProductPropertiesRulePartialInput, BulkProductPropertyInput
from properties.models import PropertyTranslation, PropertySelectValueTranslation
from properties.signals import property_created, property_select_value_created
from translations.schema.mutations import TranslatableCreateMutation


def create_property():
    extensions = []
    return TranslatableCreateMutation(PropertyInput,
        extensions=extensions,
        translation_model=PropertyTranslation,
        translation_field='name',
        translation_model_to_model_field='property',
        signal=property_created)


def create_property_select_value():
    extensions = []
    return TranslatableCreateMutation(PropertySelectValueInput,
        extensions=extensions,
        translation_model=PropertySelectValueTranslation,
        translation_field='value',
        translation_model_to_model_field='propertyselectvalue',
        signal=property_select_value_created)


def complete_create_product_properties_rule():
    extensions = []
    return CompleteCreateProductPropertiesRule(ProductPropertiesRuleInput, extensions=extensions)


def complete_update_product_properties_rule():
    extensions = []
    return CompleteUpdateProductPropertiesRule(ProductPropertiesRulePartialInput, extensions=extensions)


def bulk_create_product_properties():
    extensions = []
    return BulkCreateProductProperties(List[BulkProductPropertyInput], extensions=extensions)
