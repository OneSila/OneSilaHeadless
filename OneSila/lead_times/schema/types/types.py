from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, \
    strawberry_type, field

from typing import List

from lead_times.models import LeadTime, LeadTimeTranslation
from .filters import LeadTimeFilter, LeadTimeTranslationFilter
from .ordering import LeadTimeOrder, LeadTimeTranslationOrder


@type(LeadTime, filters=LeadTimeFilter, order=LeadTimeOrder, pagination=True, fields="__all__")
class LeadTimeType(relay.Node, GetQuerysetMultiTenantMixin):
    @field
    def name(self) -> str | None:
        return self.name


@type(LeadTimeTranslation, filters=LeadTimeTranslationFilter, order=LeadTimeTranslationOrder, pagination=True, fields="__all__")
class LeadTimeTranslationType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@strawberry_type
class LeadTimeUnitType:
    code: str
    name: str
