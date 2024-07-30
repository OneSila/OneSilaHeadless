from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from lead_times.models import LeadTime, LeadTimeTranslation, LeadTimeForShippingAddress


@order(LeadTime)
class LeadTimeOrder:
    name: auto


@order(LeadTimeTranslation)
class LeadTimeTranslationOrder:
    language: auto


@order(LeadTimeForShippingAddress)
class LeadTimeForShippingAddressOrder:
    shippingaddress: auto
    leadtime: auto
