from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from products_inspector.models import Inspector


@order(Inspector)
class InspectorOrder:
    id: auto
