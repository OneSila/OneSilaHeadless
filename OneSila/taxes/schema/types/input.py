from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial

from taxes.models import Tax


@input(Tax, fields="__all__")
class TaxInput:
    pass


@partial(Tax, fields="__all__")
class TaxPartialInput(NodeInput):
    pass
