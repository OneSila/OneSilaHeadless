from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, \
    strawberry_type, field

from typing import List

from lead_times.models import LeadTime, LeadTimeForShippingAddress
from products.schema.types.types import ProductType
from .filters import LeadTimeFilter, LeadTimeForShippingAddressFilter
from .ordering import LeadTimeOrder, LeadTimeForShippingAddressOrder
from contacts.schema.types.types import ShippingAddressType


@type(LeadTime, filters=LeadTimeFilter, order=LeadTimeOrder, pagination=True, fields="__all__")
class LeadTimeType(relay.Node, GetQuerysetMultiTenantMixin):

    @field()
    def name(self, info) -> str | None:
        return self.name


@type(LeadTimeForShippingAddress, filters=LeadTimeForShippingAddressFilter, order=LeadTimeForShippingAddressOrder, pagination=True, fields="__all__")
class LeadTimeForShippingAddressType(relay.Node, GetQuerysetMultiTenantMixin):
    leadtime: LeadTimeType
    shippingaddress: ShippingAddressType


@strawberry_type
class LeadTimeUnitType:
    code: str
    name: str
