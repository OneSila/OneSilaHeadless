from core.schema.types.types import auto
from core.schema.types.filters import filter

from taxes.models import Tax


@filter(Tax)
class TaxFilter:
    id: auto
    name: auto
    rate: auto
