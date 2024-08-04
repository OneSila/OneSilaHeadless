from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type, \
    anonymous_field
from typing import List

from .types.types import LeadTimeType, LeadTimeUnitType, LeadTimeForShippingAddressType, \
    LeadTimeProductOutOfStockType
from lead_times.models import LeadTime, LeadTimeForShippingAddress, LeadTimeProductOutOfStock


def get_lead_time_units() -> List[LeadTimeUnitType]:
    return [LeadTimeUnitType(code=code, name=name) for code, name in LeadTime.UNIT_CHOICES]


@type(name="Query")
class LeadTimesQuery:
    lead_time: LeadTimeType = node()
    lead_times: ListConnectionWithTotalCount[LeadTimeType] = connection()

    lead_time_units: List[LeadTimeUnitType] = anonymous_field(resolver=get_lead_time_units)

    lead_time_for_shippingaddress: LeadTimeForShippingAddressType = node()
    lead_time_for_shippingaddresses: ListConnectionWithTotalCount[LeadTimeForShippingAddressType] = connection()

    lead_time_product_out_of_stock: LeadTimeProductOutOfStockType = node()
    lead_time_products_out_of_stock: ListConnectionWithTotalCount[LeadTimeProductOutOfStockType] = connection()
