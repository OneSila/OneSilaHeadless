from core.schema.core.mutations import delete, type, List
from .fields import update, create
from ..types.types import CurrencyType

@type(name="Mutation")
class CurrenciesMutation:
    create_currency: CurrencyType = create()
    update_currency: CurrencyType = update()
    create_currencies: List[CurrencyType] = create()
    delete_currency: CurrencyType = delete()
    delete_currencies: List[CurrencyType] = delete()
