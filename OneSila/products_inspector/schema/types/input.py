from typing import List

from core.schema.core.types.input import partial, NodeInput, strawberry_input
from products.schema.types.input import ProductPartialInput
from products_inspector.models import Inspector


@partial(Inspector, fields="__all__")
class InspectorPartialInput(NodeInput):
    pass


@strawberry_input
class BulkRefreshInspectorInput:
    products: List[ProductPartialInput]
