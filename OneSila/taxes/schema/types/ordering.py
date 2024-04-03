from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from taxes.models import VatRate


@order(VatRate)
class VatRateOrder:
    name: auto
    rate: auto
