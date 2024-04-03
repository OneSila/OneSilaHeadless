from core.schema.core.mutations import type
from core.schema.core.mutations import create, update, delete, type, List

from .types.types import VatRateType
from .types.input import VatRateInput, VatRatePartialInput


@type(name="Mutation")
class TaxesMutation:
    create_vat_rate: VatRateType = create(VatRateInput)
    create_vat_rates: List[VatRateType] = create(VatRateInput)
    update_vat_rate: VatRateType = update(VatRatePartialInput)
    delete_vat_rate: VatRateType = delete()
    delete_vat_rates: List[VatRateType] = delete()
