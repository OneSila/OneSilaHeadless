from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import TaxType


@type(name="Query")
class TaxesQuery:
    tax: TaxType = node()
    taxes: ListConnectionWithTotalCount[TaxType] = connection()
