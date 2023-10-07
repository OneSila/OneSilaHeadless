from core.schema.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import CurrencyType


@type(name="Query")
class CurrenciesQuery:
    currency: CurrencyType = node()
    currencies: ListConnectionWithTotalCount[CurrencyType] = connection()
