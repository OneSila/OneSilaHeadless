from core.schema.types.types import auto
from core.schema.types.filters import filter

from currencies.models import Currency


@filter(Currency)
class CurrencyFilter:
    id: auto
    iso_code: auto
    name: auto
    symbol: auto
