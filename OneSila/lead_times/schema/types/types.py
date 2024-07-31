from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, \
    strawberry_type, field

from typing import List

from lead_times.models import LeadTime, LeadTimeForShippingAddress
from .filters import LeadTimeFilter, LeadTimeForShippingAddressFilter
from .ordering import LeadTimeOrder, LeadTimeForShippingAddressOrder


@type(LeadTime, filters=LeadTimeFilter, order=LeadTimeOrder, pagination=True, fields="__all__")
class LeadTimeType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(LeadTimeForShippingAddress, filters=LeadTimeForShippingAddressFilter, order=LeadTimeForShippingAddressOrder, pagination=True, fields="__all__")
class LeadTimeForShippingAddressType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@strawberry_type
class LeadTimeUnitType:
    code: str
    name: str
