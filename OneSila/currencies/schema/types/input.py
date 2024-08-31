from typing import Optional
import strawberry_django
from strawberry import ID
from strawberry_django import NodeInput

from currencies.models import Currency
from currencies.schema.types.types import PublicCurrencyType


@strawberry_django.input(Currency, fields=["id"])
class PublicCurrencyIdInput(NodeInput):
    pass


@strawberry_django.input(Currency, exclude=['iso_code', 'name', 'symbol'])
class CurrencyInput:
    public_currency: Optional[PublicCurrencyIdInput] = None


@strawberry_django.partial(Currency, fields="__all__")
class CurrencyPartialInput(NodeInput):
    public_currency: Optional[PublicCurrencyIdInput] = None
