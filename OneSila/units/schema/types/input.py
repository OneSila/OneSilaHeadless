from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial

from units.models import Unit


@input(Unit, fields="__all__")
class UnitInput:
    pass


@partial(Unit, fields="__all__")
class UnitPartialInput(NodeInput):
    pass
