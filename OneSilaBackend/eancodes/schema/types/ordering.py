from core.schema.types.ordering import order
from core.schema.types.types import auto

from eancodes.models import EanCode


@order(EanCode)
class EanCodeOrder:
    id: auto
    ean_code: auto
    product: auto
