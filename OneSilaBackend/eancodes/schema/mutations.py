from core.schema.mutations import type
from core.schema.mutations import create, update, delete, type, List

from .types.types import EanCodeType
from .types.input import EanCodeInput, EanCodePartialInput


@type(name="Mutation")
class EanCodesMutation:
    create_ean_code: EanCodeType = create(EanCodeInput)
    create_ean_codes: List[EanCodeType] = create(EanCodeInput)
    update_ean_code: EanCodeType = update(EanCodePartialInput)
    delete_ean_code: EanCodeType = delete()
    delete_ean_codes: List[EanCodeType] = delete()
