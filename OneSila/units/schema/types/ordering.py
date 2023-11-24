from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from units.models import Unit


@order(Unit)
class UnitOrder:
    name: auto
