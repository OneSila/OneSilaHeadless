from core.schema.core.mutations import type
from core.schema.core.mutations import create, update, delete, type, List

from .types.types import TaxType
from .types.input import TaxInput, TaxPartialInput


@type(name="Mutation")
class TaxesMutation:
    create_tax: TaxType = create(TaxInput)
    create_taxes: List[TaxType] = create(TaxInput)
    update_tax: TaxType = update(TaxPartialInput)
    delete_tax: TaxType = delete()
    delete_taxes: List[TaxType] = delete()
