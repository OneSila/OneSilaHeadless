from core.schema.types.types import auto
from core.schema.types.input import NodeInput, input, partial

from units.models import Unit


@input(Unit, fields="__all__")
class UnitInput:
    pass


@partial(Unit, fields="__all__")
class UnitPartialInput(NodeInput):
    pass
