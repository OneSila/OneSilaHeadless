import strawberry
import strawberry_django
from strawberry_django import NodeInput

from currencies.models import Currency


@strawberry_django.input(Currency, fields="__all__")
class CurrencyInput:
    pass


@strawberry_django.partial(Currency, fields="__all__")
class CurrencyPartialInput(NodeInput):
    pass
