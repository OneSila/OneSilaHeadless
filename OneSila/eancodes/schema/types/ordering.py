from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from eancodes.models import EanCode


@order(EanCode)
class EanCodeOrder:
    id: auto
    ean_code: auto
    product: auto
