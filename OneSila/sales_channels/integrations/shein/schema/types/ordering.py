"""Ordering definitions for Shein GraphQL types."""

from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from sales_channels.integrations.shein.models import (
    SheinRemoteCurrency,
    SheinSalesChannel,
    SheinSalesChannelView,
)


@order(SheinSalesChannel)
class SheinSalesChannelOrder:
    id: auto


@order(SheinSalesChannelView)
class SheinSalesChannelViewOrder:
    id: auto


@order(SheinRemoteCurrency)
class SheinRemoteCurrencyOrder:
    id: auto

