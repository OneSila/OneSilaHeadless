from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin
from lead_times.models import LeadTime, LeadTimeForShippingAddress, LeadTimeProductOutOfStock
from contacts.schema.types.filters import ShippingAddressFilter
from products.schema.types.filters import ProductFilter


@filter(LeadTime)
class LeadTimeFilter(SearchFilterMixin):
    search: str | None
    id: auto


@filter(LeadTimeForShippingAddress)
class LeadTimeForShippingAddressFilter(SearchFilterMixin):
    search: str | None
    leadtime: LeadTimeFilter | None
    shippingaddress: ShippingAddressFilter | None


@filter(LeadTimeProductOutOfStock)
class LeadTimeProductOutOfStockFilter(SearchFilterMixin):
    search: str | None
    leadtime_outofstock: LeadTimeFilter | None
    product: ProductFilter | None
