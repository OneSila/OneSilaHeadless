from .mutation_classes import UpdateWithPublicIdMutation, CreateWithPublicIdMutation
from ..types.input import CurrencyPartialInput, CurrencyInput

def create():
    extensions = []
    return CreateWithPublicIdMutation(CurrencyInput, extensions=extensions)

def update():
    extensions = []
    return UpdateWithPublicIdMutation(CurrencyPartialInput, extensions=extensions)