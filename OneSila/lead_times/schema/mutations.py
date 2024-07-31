from core.schema.core.mutations import type
from core.schema.core.mutations import create, update, delete, type, List

from .types.types import LeadTimeType, LeadTimeForShippingAddressType
from .types.input import LeadTimeInput, LeadTimePartialInput, \
    LeadTimeForShippingAddressInput, LeadTimeForShippingAddressPartialInput


@type(name="Mutation")
class LeadTimesMutation:
    create_lead_time: LeadTimeType = create(LeadTimeInput)
    create_lead_times: List[LeadTimeType] = create(LeadTimeInput)
    update_lead_time: LeadTimeType = update(LeadTimePartialInput)
    delete_lead_time: LeadTimeType = delete()
    delete_lead_times: List[LeadTimeType] = delete()

    create_lead_time_for_shippingaddress: LeadTimeForShippingAddressType = create(LeadTimeForShippingAddressInput)
    create_lead_time_for_shippingaddresses: List[LeadTimeForShippingAddressType] = create(LeadTimeForShippingAddressInput)
    update_lead_time_for_shippingaddress: LeadTimeForShippingAddressType = update(LeadTimeForShippingAddressPartialInput)
    delete_lead_time_for_shippingaddress: LeadTimeForShippingAddressType = delete()
    delete_lead_times_for_shippingaddress: List[LeadTimeForShippingAddressType] = delete()
