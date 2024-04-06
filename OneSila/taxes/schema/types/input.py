from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial

from taxes.models import VatRate


@input(VatRate, fields="__all__")
class VatRateInput:
    pass


@partial(VatRate, fields="__all__")
class VatRatePartialInput(NodeInput):
    pass
