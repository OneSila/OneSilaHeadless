from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import CurrencyType, PublicCurrencyType


@type(name="Query")
class CurrenciesQuery:
    currency: CurrencyType = node()
    currencies: ListConnectionWithTotalCount[CurrencyType] = connection()

    public_currencies: ListConnectionWithTotalCount[PublicCurrencyType] = connection()
