from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, Optional

from eancodes.models import EanCode
from products.schema.types.filters import ProductFilter


@filter(EanCode)
class EanCodeFilter(SearchFilterMixin):
    search: Optional[str]
    id: auto
    ean_code: auto
    product: Optional[ProductFilter]
