from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, \
    strawberry_type, field

from typing import List

from lead_times.models import LeadTime, LeadTimeForShippingAddress, LeadTimeProductOutOfStock
from .filters import LeadTimeFilter, LeadTimeForShippingAddressFilter, LeadTimeProductOutOfStockFilter
from .ordering import LeadTimeOrder, LeadTimeForShippingAddressOrder, LeadTimeProductOutOfStockOrder


@type(LeadTime, filters=LeadTimeFilter, order=LeadTimeOrder, pagination=True, fields="__all__")
class LeadTimeType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(LeadTimeForShippingAddress, filters=LeadTimeForShippingAddressFilter, order=LeadTimeForShippingAddressOrder, pagination=True, fields="__all__")
class LeadTimeForShippingAddressType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(LeadTimeProductOutOfStock, filters=LeadTimeProductOutOfStockFilter, order=LeadTimeProductOutOfStockOrder, pagination=True, fields="__all__")
class LeadTimeProductOutOfStockType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@strawberry_type
class LeadTimeUnitType:
    code: str
    name: str
