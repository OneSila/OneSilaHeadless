"""Filter definitions for Shein GraphQL types."""

from typing import Optional

from core.schema.core.types.filters import SearchFilterMixin, filter
from core.schema.core.types.types import auto
from currencies.schema.types.filters import CurrencyFilter
from sales_channels.integrations.shein.models import (
    SheinRemoteCurrency,
    SheinSalesChannel,
    SheinSalesChannelView,
)
from sales_channels.schema.types.filters import SalesChannelFilter


@filter(SheinSalesChannel)
class SheinSalesChannelFilter(SearchFilterMixin):
    """Filter Shein sales channels by basic attributes."""

    id: auto
    hostname: auto
    active: auto


@filter(SheinSalesChannelView)
class SheinSalesChannelViewFilter(SearchFilterMixin):
    """Filter Shein storefront mirrors."""

    id: auto
    sales_channel: Optional[SalesChannelFilter]
    is_default: auto
    store_type: auto
    site_status: auto


@filter(SheinRemoteCurrency)
class SheinRemoteCurrencyFilter(SearchFilterMixin):
    """Filter Shein remote currencies and their local mappings."""

    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[CurrencyFilter]
    remote_code: auto

