from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from eancodes.models import EanCode
from products.schema.types.filters import ProductFilter


@filter(EanCode)
class EanCodeFilter(SearchFilterMixin):
    search: str | None
    id: auto
    ean_code: auto
    product: ProductFilter
