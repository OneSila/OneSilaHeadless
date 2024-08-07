from typing import Optional

from core.schema.core.mutations import type
from core.schema.core.mutations import create, update, delete, type, List
from .fields import generate_eancodes, assign_ean_code, release_ean_code
from ..types.types import EanCodeType
from ..types.input import EanCodeInput, EanCodePartialInput


@type(name="Mutation")
class EanCodesMutation:
    create_ean_code: EanCodeType = create(EanCodeInput)
    create_ean_codes: List[EanCodeType] = create(EanCodeInput)
    update_ean_code: EanCodeType = update(EanCodePartialInput)
    delete_ean_code: EanCodeType = delete()
    delete_ean_codes: List[EanCodeType] = delete()

    generate_ean_codes: Optional[EanCodeType] = generate_eancodes()
    assign_ean_code: EanCodeType = assign_ean_code()
    release_ean_code: EanCodeType = release_ean_code()
