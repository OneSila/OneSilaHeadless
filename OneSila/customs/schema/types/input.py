from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial, List

from customs.models import HsCode
from products.schema.types.input import ProductPartialInput


@input(HsCode, fields="__all__")
class HsCodeInput:
    product: List[ProductPartialInput] | None


@partial(HsCode, fields="__all__")
class HsCodePartialInput(NodeInput):
    product: List[ProductPartialInput] | None
