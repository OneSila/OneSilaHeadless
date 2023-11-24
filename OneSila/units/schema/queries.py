from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import UnitType


@type(name="Query")
class UnitsQuery:
    unit: UnitType = node()
    units: ListConnectionWithTotalCount[UnitType] = connection()
