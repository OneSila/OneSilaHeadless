from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter

from units.models import Unit


@filter(Unit)
class UnitFilter:
    id: auto
    name: auto
