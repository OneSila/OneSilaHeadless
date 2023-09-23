from core.schema.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import EanCodeType


@type(name="Query")
class EanCodeQuery:
    ean_code: EanCodeType = node()
    ean_codes: ListConnectionWithTotalCount[EanCodeType] = connection()
