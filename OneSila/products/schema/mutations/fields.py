from products.models import ProductTranslation
from products.schema.mutations.mutation_classes import AliasProductCreateMutation
from products.schema.types.input import ProductInput


def create_product():
    extensions = []
    return AliasProductCreateMutation(
        ProductInput,
        extensions=extensions,
        translation_model=ProductTranslation,
        translation_field='name',
        translation_model_to_model_field='product'
    )
