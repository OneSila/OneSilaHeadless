from .mutation_classes import CreateWithOwnerMutation
from products.schema.types.input import ProductInput


def create(input_type):
    extensions = []
    return CreateWithOwnerMutation(input_type, extensions=extensions)