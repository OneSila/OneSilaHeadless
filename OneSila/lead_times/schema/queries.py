from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type, \
    anonymous_field
from typing import List

from .types.types import LeadTimeType, LeadTimeTranslationType, LeadTimeUnitType, LeadTimeForShippingAddressType
from lead_times.models import LeadTime, LeadTimeForShippingAddress


def get_lead_time_units() -> List[LeadTimeUnitType]:
    return [LeadTimeUnitType(code=code, name=name) for code, name in LeadTime.UNIT_CHOICES]


@type(name="Query")
class LeadTimesQuery:
    lead_time: LeadTimeType = node()
    lead_times: ListConnectionWithTotalCount[LeadTimeType] = connection()

    lead_time_translation: LeadTimeTranslationType = node()
    lead_time_translations: ListConnectionWithTotalCount[LeadTimeTranslationType] = connection()

    lead_time_units: List[LeadTimeUnitType] = anonymous_field(resolver=get_lead_time_units)

    lead_time_for_shippingaddress: LeadTimeForShippingAddressType = node()
    lead_time_for_shippingaddresses: ListConnectionWithTotalCount[LeadTimeForShippingAddressType] = connection()
