from core.schema.core.types.filters import filter, SearchFilterMixin
from core.schema.core.types.types import auto
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProperty,
    AmazonPropertySelectValue,
)


@filter(AmazonSalesChannel)
class AmazonSalesChannelFilter(SearchFilterMixin):
    active: auto
    hostname: auto


@filter(AmazonProperty)
class AmazonPropertyFilter(SearchFilterMixin):
    pass


@filter(AmazonPropertySelectValue)
class AmazonPropertySelectValueFilter(SearchFilterMixin):
    pass