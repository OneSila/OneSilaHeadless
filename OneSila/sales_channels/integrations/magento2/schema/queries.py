import json
from typing import List
from strawberry import Info, ID
from core.schema.core.helpers import get_multi_tenant_company
from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type, field
from sales_channels.integrations.magento2.constants import EXCLUDED_ATTRIBUTE_CODES
from sales_channels.integrations.magento2.factories.sales_channels.sales_channel import TryConnection
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.integrations.magento2.schema.types.types import MagentoRemoteAttributeType, MagentoSalesChannelType, \
    MagentoRemoteAttributeSetType
from strawberry.relay import from_base64


def get_magento_attributes(info: Info, sales_channel_id: ID) -> List[MagentoRemoteAttributeType]:
    multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

    type_name, db_id = from_base64(sales_channel_id)

    try:
        sales_channel = MagentoSalesChannel.objects.get(
            id=db_id,
            multi_tenant_company=multi_tenant_company
        )
    except MagentoSalesChannel.DoesNotExist:
        raise Exception("Sales channel not found")

    api = TryConnection(sales_channel=sales_channel).api
    attributes = api.product_attributes.all_in_memory()

    return [
        MagentoRemoteAttributeType(
            id=attr.attribute_id,
            attribute_code=attr.attribute_code,
            name=attr.default_frontend_label,
            data=json.dumps(attr.data)
        )
        for attr in attributes
        if hasattr(attr, 'default_frontend_label')
           and attr.attribute_code not in EXCLUDED_ATTRIBUTE_CODES
    ]


def get_magento_attribute_sets(info: Info, sales_channel_id: ID) -> list[MagentoRemoteAttributeSetType]:
    multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

    type_name, db_id = from_base64(sales_channel_id)

    try:
        sales_channel = MagentoSalesChannel.objects.get(
            id=db_id,
            multi_tenant_company=multi_tenant_company
        )
    except MagentoSalesChannel.DoesNotExist:
        raise Exception("Sales channel not found")

    api = TryConnection(sales_channel=sales_channel).api
    attribute_sets = api.product_attribute_set.all_in_memory()

    return [
        MagentoRemoteAttributeSetType(
            id=str(attr.attribute_set_id),
            name=attr.attribute_set_name,
        )
        for attr in attribute_sets
    ]

@type(name="Query")
class MagentoSalesChannelsQuery:
    magento_remote_attributes: List[MagentoRemoteAttributeType] = field(
        resolver=get_magento_attributes)
    magento_remote_attribute_sets: List[MagentoRemoteAttributeSetType] = field(
        resolver=get_magento_attribute_sets
    )

    magento_channel: MagentoSalesChannelType = node()
    magento_channels: ListConnectionWithTotalCount[MagentoSalesChannelType] = connection()