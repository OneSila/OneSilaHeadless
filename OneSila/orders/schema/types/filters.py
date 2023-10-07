from core.schema.types.types import auto
from core.schema.types.filters import filter

from orders.models import Order, OrderItem, OrderNote
from products.schema.types.filters import ProductFilter


@filter(Order)
class OrderFilter:
    id: auto
    reference: auto
    company: auto
    invoice_address: auto
    shipping_address: auto
    currency: auto
    status: auto
    reason_for_sale: auto


@filter(OrderItem)
class OrderItemFilter:
    id: auto
    order: OrderFilter
    product: ProductFilter


@filter(OrderNote)
class OrderNoteFilter:
    id: auto
    order: OrderFilter
