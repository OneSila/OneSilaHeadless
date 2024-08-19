from properties.schema.mutations.mutation_classes import CompleteCreateProductPropertiesRule, CompleteUpdateProductPropertiesRule
from properties.schema.types.input import PropertyInput, PropertySelectValueInput, ProductPropertiesRuleInput, ProductPropertiesRulePartialInput
from properties.models import PropertyTranslation, PropertySelectValueTranslation
from translations.schema.mutations import TranslatableCreateMutation


def create_property():
    extensions = []
    return TranslatableCreateMutation(PropertyInput,
        extensions=extensions,
        translation_model=PropertyTranslation,
        translation_field='name',
        translation_model_to_model_field='property')


def create_property_select_value():
    extensions = []
    return TranslatableCreateMutation(PropertySelectValueInput,
        extensions=extensions,
        translation_model=PropertySelectValueTranslation,
        translation_field='value',
        translation_model_to_model_field='propertyselectvalue')


def complete_create_product_properties_rule():
    extensions = []
    return CompleteCreateProductPropertiesRule(ProductPropertiesRuleInput, extensions=extensions)

def complete_update_product_properties_rule():
    extensions = []
    return CompleteUpdateProductPropertiesRule(ProductPropertiesRulePartialInput, extensions=extensions)

