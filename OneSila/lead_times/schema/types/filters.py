from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from lead_times.models import LeadTime, LeadTimeForShippingAddress


@filter(LeadTime)
class LeadTimeFilter(SearchFilterMixin):
    search: str | None
    id: auto


@filter(LeadTimeForShippingAddress)
class LeadTimeForShippingAddressFilter(SearchFilterMixin):
    search: str | None
    leadtime: auto
    shippingaddress: auto
