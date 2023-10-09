from core.schema.types.ordering import order
from core.schema.types.types import auto

from customs.models import HsCode


@order(HsCode)
class HsCodeOrder:
    name: auto
    code: auto
