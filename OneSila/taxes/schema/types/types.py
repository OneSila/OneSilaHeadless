from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin

from typing import List

from taxes.models import VatRate
from .filters import VatRateFilter
from .ordering import VatRateOrder


@type(VatRate, filters=VatRateFilter, order=VatRateOrder, pagination=True, fields="__all__")
class VatRateType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
