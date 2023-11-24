from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial

from customs.models import HsCode


@input(HsCode, fields="__all__")
class HsCodeInput:
    pass


@partial(HsCode, fields="__all__")
class HsCodePartialInput:
    pass
