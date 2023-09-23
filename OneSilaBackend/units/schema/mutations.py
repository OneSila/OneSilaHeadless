from core.schema.mutations import type
from core.schema.mutations import create, update, delete, type, List

from .types.types import UnitType
from .types.input import UnitInput, UnitPartialInput


@type(name="Mutation")
class Mutation:
    create_unit: UnitType = create(UnitInput)
    create_units: List[UnitType] = create(UnitInput)
    update_unit: UnitType = update(UnitPartialInput)
    delete_unit: UnitType = delete()
    delete_units: ListUnit[Type] = delete()
