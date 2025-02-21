from products.models import ProductTranslation
from products.schema.types.input import ProductInput
from translations.schema.mutations import TranslatableCreateMutation


def create_product():
    extensions = []
    return TranslatableCreateMutation(ProductInput,
        extensions=extensions,
        translation_model=ProductTranslation,
        translation_field='name',
        translation_model_to_model_field='product')