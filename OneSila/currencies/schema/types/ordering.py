from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from currencies.models import Currency


@order(Currency)
class CurrencyOrder:
    iso_code: auto
    name: auto
