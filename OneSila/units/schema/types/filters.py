from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from units.models import Unit


@filter(Unit)
class UnitFilter(SearchFilterMixin):
    search: str | None
    id: auto
    name: auto
