from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from currencies.models import Currency


@filter(Currency)
class CurrencyFilter(SearchFilterMixin):
    id: auto
    iso_code: auto
    is_default_currency: auto
    name: auto
    symbol: auto
