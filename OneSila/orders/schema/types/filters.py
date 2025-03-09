from typing import Optional
from strawberry.relay import GlobalID

from contacts.schema.types.filters import CustomerFilter
from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, lazy, ExcluideDemoDataFilterMixin

from orders.models import Order, OrderItem, OrderNote
from products.schema.types.filters import ProductFilter


@filter(Order)
class OrderFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    reference: auto
    currency: auto
    orderitem: Optional[lazy['OrderItemFilter', "orders.schema.types.filters"]]


@filter(OrderItem)
class OrderItemFilter(SearchFilterMixin):
    id: auto
    order: OrderFilter | None
    product: ProductFilter | None


@filter(OrderNote)
class OrderNoteFilter(SearchFilterMixin):
    id: auto
    order: OrderFilter | None
