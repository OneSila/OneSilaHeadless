from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from lead_times.models import LeadTime, LeadTimeTranslation


@filter(LeadTime)
class LeadTimeFilter(SearchFilterMixin):
    search: str | None
    id: auto


@filter(LeadTimeTranslation)
class LeadTimeTranslationFilter(SearchFilterMixin):
    search: str | None
    id: auto
    name: auto
    language: auto
