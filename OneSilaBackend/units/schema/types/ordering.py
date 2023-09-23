from core.schema.types.ordering import order
from core.schema.types.types import auto

from units.models import Unit


@order(Unit)
class Order:
    name: auto
