from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from customs.models import HsCode


@order(HsCode)
class HsCodeOrder:
    name: auto
    code: auto
