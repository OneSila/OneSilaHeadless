from core.schema.core.queries import node, connection, DjangoListConnection, type
from typing import List

from .types.types import UnitType


@type(name="Query")
class UnitsQuery:
    unit: UnitType = node()
    units: DjangoListConnection[UnitType] = connection()
