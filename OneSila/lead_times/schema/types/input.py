from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial

from lead_times.models import LeadTime, LeadTimeForShippingAddress


@input(LeadTime, fields="__all__")
class LeadTimeInput:
    pass


@partial(LeadTime, fields="__all__")
class LeadTimePartialInput(NodeInput):
    pass


@input(LeadTimeForShippingAddress, fields="__all__")
class LeadTimeForShippingAddressInput:
    pass


@partial(LeadTimeForShippingAddress, fields="__all__")
class LeadTimeForShippingAddressPartialInput(NodeInput):
    pass
