from core.schema.core.queries import node, connection, DjangoListConnection, type
from typing import List

from .types.types import EanCodeType


@type(name="Query")
class EanCodesQuery:
    ean_code: EanCodeType = node()
    ean_codes: DjangoListConnection[EanCodeType] = connection()
