from core.schema.core.types.filters import filter, SearchFilterMixin
from core.schema.core.types.types import auto
from imports_exports.models import Import


@filter(Import)
class ImportFilter(SearchFilterMixin):
    id: auto