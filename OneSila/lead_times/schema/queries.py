from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import LeadTimeType, LeadTimeTranslatinType


@type(name="Query")
class LeadTimesQuery:
    lead_time: LeadTimeType = node()
    lead_times: ListConnectionWithTotalCount[LeadTimeType] = connection()

    lead_time_translation: LeadTimeTranslatinType = node()
    lead_time_translations: ListConnectionWithTotalCount[LeadTimeTranslatinType] = connection()
