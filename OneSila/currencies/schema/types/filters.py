from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from currencies.models import Currency


@filter(Currency)
class CurrencyFilter(SearchFilterMixin):
    search: str | None
    id: auto
    iso_code: auto
    name: auto
    symbol: auto
