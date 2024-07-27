from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial

from lead_times.models import LeadTime, LeadTimeTranslation


@input(LeadTime, fields="__all__")
class LeadTimeInput:
    name: str


@partial(LeadTime, fields="__all__")
class LeadTimePartialInput(NodeInput):
    pass


@input(LeadTimeTranslation, fields="__all__")
class LeadTimeTranslationInput:
    pass


@partial(LeadTimeTranslation, fields="__all__")
class LeadTimeTranslationPartialInput(NodeInput):
    pass
