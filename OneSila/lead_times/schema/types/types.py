from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, \
    strawberry_type, field

from typing import List

from lead_times.models import LeadTime, LeadTimeForShippingAddress, LeadTimeProductOutOfStock
from products.schema.types.types import ProductType
from .filters import LeadTimeFilter, LeadTimeForShippingAddressFilter, LeadTimeProductOutOfStockFilter
from .ordering import LeadTimeOrder, LeadTimeForShippingAddressOrder, LeadTimeProductOutOfStockOrder
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


@type(LeadTimeProductOutOfStock, filters=LeadTimeProductOutOfStockFilter, order=LeadTimeProductOutOfStockOrder, pagination=True, fields="__all__")
class LeadTimeProductOutOfStockType(relay.Node, GetQuerysetMultiTenantMixin):
    product: ProductType
    leadtime_outofstock: LeadTimeType


@strawberry_type
class LeadTimeUnitType:
    code: str
    name: str
