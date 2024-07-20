from properties.schema.mutations.mutation_classes import CreatePropertyMutation, CreatePropertySelectValueMutation
from properties.schema.types.input import PropertyInput, PropertySelectValueInput


def create_property():
    extensions = []
    return CreatePropertyMutation(PropertyInput, extensions=extensions)


def create_property_select_value():
    extensions = []
    return CreatePropertySelectValueMutation(PropertySelectValueInput, extensions=extensions)
