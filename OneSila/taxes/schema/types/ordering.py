from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from taxes.models import Tax


@order(Tax)
class TaxOrder:
    name: auto
    rate: auto
