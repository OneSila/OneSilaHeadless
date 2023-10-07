from core.schema.types.types import auto
from core.schema.types.filters import filter

from eancodes.models import EanCode
from products.schema.types.filters import ProductFilter


@filter(EanCode)
class EanCodeFilter:
    id: auto
    ean_code: auto
    product: ProductFilter
