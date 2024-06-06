from typing import Optional

import strawberry_django
from strawberry import UNSET
from strawberry.relay import GlobalID

from contacts.schema.types.filters import CustomerFilter
from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from orders.models import Order, OrderItem, OrderNote
from products.schema.types.filters import ProductFilter


@filter(Order)
class OrderFilter(SearchFilterMixin):
    search: str | None
    id: auto
    reference: auto
    customer: CustomerFilter | None
    invoice_address: auto
    shipping_address: auto
    currency: auto
    status: auto
    reason_for_sale: auto
    product_item_id: Optional[GlobalID]
    orderitem: Optional['OrderItemFilter']


@filter(OrderItem)
class OrderItemFilter(SearchFilterMixin):
    search: str | None
    id: auto
    order: OrderFilter | None
    product: ProductFilter | None


@filter(OrderNote)
class OrderNoteFilter(SearchFilterMixin):
    search: str | None
    id: auto
    order: OrderFilter | None
