from products.schema.mutations.mutation_classes import CreateProductMutation, CreateSupplierProductMutation
from products.schema.types.input import ProductInput, SupplierProductInput


def create_product():
    extensions = []
    return CreateProductMutation(ProductInput, extensions=extensions)

def create_supplier_product():
    extensions = []
    return CreateSupplierProductMutation(SupplierProductInput, extensions=extensions)