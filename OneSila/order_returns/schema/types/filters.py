from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from order_returns.models import OrderReturn, OrderReturnItem


@filter(OrderReturn)
class OrderReturnFilter(SearchFilterMixin):
    status: auto
    received_on: auto


@filter(OrderReturnItem)
class OrderReturnItemFilter(SearchFilterMixin):
    pass
