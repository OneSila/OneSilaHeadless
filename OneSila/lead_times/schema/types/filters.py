from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin
from lead_times.models import LeadTime, LeadTimeForShippingAddress, LeadTimeProductOutOfStock
from contacts.schema.types.filters import ShippingAddressFilter
from products.schema.types.filters import ProductFilter


@filter(LeadTime)
class LeadTimeFilter(SearchFilterMixin):
    id: auto


@filter(LeadTimeForShippingAddress)
class LeadTimeForShippingAddressFilter(SearchFilterMixin):
    id: auto
    leadtime: LeadTimeFilter | None
    shippingaddress: ShippingAddressFilter | None


@filter(LeadTimeProductOutOfStock)
class LeadTimeProductOutOfStockFilter(SearchFilterMixin):
    leadtime_outofstock: LeadTimeFilter | None
    product: ProductFilter | None
