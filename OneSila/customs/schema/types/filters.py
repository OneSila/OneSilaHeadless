from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from customs.models import HsCode
from products.schema.types.filters import ProductFilter


@filter(HsCode)
class HsCodeFilter(SearchFilterMixin):
    id: auto
    code: auto
    name: auto
    product: ProductFilter
