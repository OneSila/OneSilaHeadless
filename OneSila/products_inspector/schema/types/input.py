from core.schema.core.types.input import partial, NodeInput
from products_inspector.models import Inspector


@partial(Inspector, fields="__all__")
class InspectorPartialInput(NodeInput):
    pass