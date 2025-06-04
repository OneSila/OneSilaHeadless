from core.schema.core.types.filters import filter, SearchFilterMixin
from core.schema.core.types.types import auto
from sales_channels.integrations.amazon.models import AmazonSalesChannel


@filter(AmazonSalesChannel)
class AmazonSalesChannelFilter(SearchFilterMixin):
    active: auto
    hostname: auto
