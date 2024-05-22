from products.schema.mutations.mutation_classes import CreateProductMutation
from products.schema.types.input import ProductInput


def create_product():
    extensions = []
    return CreateProductMutation(ProductInput, extensions=extensions)