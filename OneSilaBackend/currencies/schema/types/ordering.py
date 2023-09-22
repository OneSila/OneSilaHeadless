from core.schema.types.ordering import order
from core.schema.types.types import auto

from currencies.models import Currency


@order(Currency)
class CurrencyOrder:
    iso_code: auto
