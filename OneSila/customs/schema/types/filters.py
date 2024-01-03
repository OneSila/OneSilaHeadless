from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from customs.models import HsCode


@filter(HsCode)
class HsCodeFilter(SearchFilterMixin):
    search: str | None
    id: auto
    code: auto
    name: auto
