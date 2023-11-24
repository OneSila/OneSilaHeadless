from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter

from taxes.models import Tax


@filter(Tax)
class TaxFilter:
    id: auto
    name: auto
    rate: auto
