from core.schema.core.queries import node, connection, DjangoListConnection, type
from typing import List

from .types.types import VatRateType


@type(name="Query")
class TaxesQuery:
    vat_rate: VatRateType = node()
    vat_rates: DjangoListConnection[VatRateType] = connection()
