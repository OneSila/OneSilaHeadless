from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin

from typing import List

from currencies.models import Currency
from .filters import CurrencyFilter
from .ordering import CurrencyOrder


@type(Currency, filters=CurrencyFilter, order=CurrencyOrder, pagination=True, fields="__all__")
class CurrencyType(relay.Node, GetQuerysetMultiTenantMixin):
    inherits_from: List['CurrencyType'] | None
