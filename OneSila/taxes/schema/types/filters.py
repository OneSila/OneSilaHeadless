from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from taxes.models import VatRate


@filter(VatRate)
class VatRateFilter(SearchFilterMixin):
    id: auto
    name: auto
    rate: auto
