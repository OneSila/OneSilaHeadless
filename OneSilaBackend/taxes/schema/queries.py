from core.schema.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import TaxType


@type(name="Query")
class TaxQuery:
    tax: TaxType = node()
    taxes: ListConnectionWithTotalCount[TaxType] = connection()
