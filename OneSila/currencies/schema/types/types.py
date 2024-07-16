from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin

from typing import Self

from currencies.models import Currency, PublicCurrency
from .filters import CurrencyFilter
from .ordering import CurrencyOrder


@type(Currency, filters=CurrencyFilter, order=CurrencyOrder, pagination=True, fields="__all__")
class CurrencyType(relay.Node, GetQuerysetMultiTenantMixin):
    inherits_from: Self | None

@type(PublicCurrency, pagination=True, fields="__all__")
class PublicCurrencyType(relay.Node):
    pass