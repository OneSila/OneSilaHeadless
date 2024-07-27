from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type, \
    anonymous_field
from typing import List

from .types.types import LeadTimeType, LeadTimeTranslationType, LeadTimeUnitType
from lead_times.models import LeadTime


def get_lead_time_units() -> List[LeadTimeUnitType]:
    return [CountryType(code=code, name=name) for code, name in LeadTime.UNIT_CHOICES]


@type(name="Query")
class LeadTimesQuery:
    lead_time: LeadTimeType = node()
    lead_times: ListConnectionWithTotalCount[LeadTimeType] = connection()

    lead_time_translation: LeadTimeTranslationType = node()
    lead_time_translations: ListConnectionWithTotalCount[LeadTimeTranslationType] = connection()

    lead_time_units: List[LeadTimeUnitType] = anonymous_field(resolver=get_lead_time_units)
