from core.schema.core.mutations import create, update, delete, type, List, field

from .types.types import HsCodeType
from .types.input import HsCodeInput, HsCodePartialInput


@type(name="Mutation")
class CustomsMutation:
    create_hs_code: HsCodeType = create(HsCodeInput)
    create_hs_codes: List[HsCodeType] = create(HsCodeInput)
    update_hs_code: HsCodeType = update(HsCodeInput)
    delete_hs_code: HsCodeType = delete()
    delete_hs_codes: List[HsCodeType] = delete()
