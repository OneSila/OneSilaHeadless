from core.schema.core.types.types import type, relay, List, Annotated, lazy
from core.schema.core.mixins import GetQuerysetMultiTenantMixin

from order_returns.models import OrderReturn, OrderReturnItem
from .filters import OrderReturnFilter, OrderReturnItemFilter
from .ordering import OrderReturnOrder, OrderReturnItemOrder


@type(OrderReturn, filters=OrderReturnFilter, order=OrderReturnOrder, pagination=True, fields='__all__')
class OrderReturnType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(OrderReturnItem, filters=OrderReturnItemFilter, order=OrderReturnItemOrder, pagination=True, fields='__all__')
class OrderReturnItemType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
