from contacts.schema.types.types import CustomerType, InvoiceAddressType, ShippingAddressType
from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field

from typing import List

from currencies.schema.types.types import CurrencyType
from orders.models import Order, OrderItem, OrderNote
from products.schema.types.types import ProductType
from .filters import OrderFilter, OrderItemFilter, OrderNoteFilter
from .ordering import OrderOrder, OrderItemOrder, OrderNoteOrder


@type(Order, filters=OrderFilter, order=OrderOrder, pagination=True, fields="__all__")
class OrderType(relay.Node, GetQuerysetMultiTenantMixin):
    customer: CustomerType
    invoice_address: InvoiceAddressType
    shipping_address: ShippingAddressType
    currency: CurrencyType
    orderitem_set: List['OrderItemType']

    @field()
    def total_value(self) -> str | None:
        return self.total_value_currency


@type(OrderItem, filters=OrderItemFilter, order=OrderItemOrder, pagination=True, fields="__all__")
class OrderItemType(relay.Node, GetQuerysetMultiTenantMixin):
    order: OrderType
    product: ProductType


@type(OrderNote, filters=OrderNoteFilter, order=OrderNoteOrder, pagination=True, fields="__all__")
class OrderNoteType(relay.Node, GetQuerysetMultiTenantMixin):
    order: OrderType
