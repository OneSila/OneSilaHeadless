from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from lead_times.models import LeadTime, LeadTimeForShippingAddress


@order(LeadTime)
class LeadTimeOrder:
    min_time: auto
    max_time: auto
    unit: auto


@order(LeadTimeForShippingAddress)
class LeadTimeForShippingAddressOrder:
    shippingaddress: auto
    leadtime: auto
