from core.schema.core.types.filters import filter, SearchFilterMixin
from core.schema.core.types.types import auto
from sales_channels.integrations.ebay.models import EbaySalesChannel


@filter(EbaySalesChannel)
class EbaySalesChannelFilter(SearchFilterMixin):
    active: auto
    hostname: auto
