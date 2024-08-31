from core.schema.core.types.input import NodeInput, input, partial
from core.schema.core.types.input import strawberry_input
from eancodes.models import EanCode
from products.schema.types.input import ProductPartialInput


@input(EanCode, fields="__all__")
class EanCodeInput:
    pass


@partial(EanCode, fields="__all__")
class EanCodePartialInput(NodeInput):
    pass


@strawberry_input
class GenerateEancodesInput:
    prefix: str

@strawberry_input
class AssignEancodeInput:
    product: ProductPartialInput