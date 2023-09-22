import strawberry_django
from strawberry import auto

from currencies.models import Currency


@strawberry_django.filters.filter(Currency, lookups=True)
class CurrencyFilter:
    id: auto
    iso_code: auto
    name: auto
    symbol: auto
