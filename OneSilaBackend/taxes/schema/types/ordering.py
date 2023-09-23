from core.schema.types.ordering import order
from core.schema.types.types import auto

from taxes.models import Tax


@order(Tax)
class TaxOrder:
    name: auto
    rate: auto
