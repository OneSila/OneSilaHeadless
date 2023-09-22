from core.schema.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from currencies.models import Currency
from .types.types import CurrencyType


@type(name="Query")
class CurrencyQuery:
    currency: CurrencyType = node()
    currencies: ListConnectionWithTotalCount[CurrencyType] = connection()
