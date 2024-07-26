from products.models import ProductTranslation
from products.schema.mutations.mutation_classes import CreateSupplierProductMutation
from products.schema.types.input import ProductInput, SupplierProductInput
from core.schema.languages.mutations import TranslatableCreateMutation


def create_product():
    extensions = []
    return TranslatableCreateMutation(ProductInput,
        extensions=extensions,
        translation_model=ProductTranslation,
        translation_field='name',
        translation_model_to_model_field='product')


def create_supplier_product():
    extensions = []
    return CreateSupplierProductMutation(SupplierProductInput, extensions=extensions)
