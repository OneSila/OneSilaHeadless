from core.schema.core.queries import node, connection, DjangoListConnection, type
from typing import List

from .types.types import CurrencyType, PublicCurrencyType


@type(name="Query")
class CurrenciesQuery:
    currency: CurrencyType = node()
    currencies: DjangoListConnection[CurrencyType] = connection()

    public_currencies: DjangoListConnection[PublicCurrencyType] = connection()
