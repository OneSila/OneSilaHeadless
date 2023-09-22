from core.schema.mutations import type
from core.schema.mutations import create, update, delete, type, List

from .types.types import CurrencyType
from .types.input import CurrencyInput, CurrencyPartialInput


@type(name="Mutation")
class CurrencyMutation:
    create_currency: CurrencyType = create(CurrencyInput)
    create_currencies: List[CurrencyType] = create(CurrencyInput)
    update_currency: CurrencyType = update(CurrencyPartialInput)
    delete_currency: CurrencyType = delete()
    delete_currencies: List[CurrencyType] = delete()
