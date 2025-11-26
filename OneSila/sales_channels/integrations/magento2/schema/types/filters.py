from core.schema.core.types.filters import filter, SearchFilterMixin
from core.schema.core.types.types import auto
from sales_channels.integrations.magento2.models import MagentoSalesChannel


@filter(MagentoSalesChannel)
class MagentoSalesChannelFilter(SearchFilterMixin):
    active: auto
