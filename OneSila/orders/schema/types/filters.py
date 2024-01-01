from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from orders.models import Order, OrderItem, OrderNote
from products.schema.types.filters import ProductFilter


@filter(Order)
class OrderFilter(SearchFilterMixin):
    search: str
    id: auto
    reference: auto
    company: auto
    invoice_address: auto
    shipping_address: auto
    currency: auto
    status: auto
    reason_for_sale: auto


@filter(OrderItem)
class OrderItemFilter(SearchFilterMixin):
    search: str
    id: auto
    order: OrderFilter
    product: ProductFilter


@filter(OrderNote)
class OrderNoteFilter(SearchFilterMixin):
    search: str
    id: auto
    order: OrderFilter
