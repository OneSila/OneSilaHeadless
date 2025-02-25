from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, ExcluideDemoDataFilterMixin

from eancodes.models import EanCode
from products.schema.types.filters import ProductFilter


@filter(EanCode)
class EanCodeFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    ean_code: auto
    internal: auto
    already_used: auto
    product: ProductFilter | None
