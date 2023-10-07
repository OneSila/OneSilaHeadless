from core.schema.types.types import auto
from core.schema.types.filters import filter

from units.models import Unit


@filter(Unit)
class UnitFilter:
    id: auto
    name: auto
