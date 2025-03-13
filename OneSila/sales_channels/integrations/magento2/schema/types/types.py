from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.integrations.magento2.schema.types.filters import MagentoSalesChannelFilter
from sales_channels.integrations.magento2.schema.types.ordering import MagentoSalesChannelOrder


@type(MagentoSalesChannel, filters=MagentoSalesChannelFilter, order=MagentoSalesChannelOrder, pagination=True, fields="__all__")
class MagentoSalesChannelType(relay.Node, GetQuerysetMultiTenantMixin):
    pass