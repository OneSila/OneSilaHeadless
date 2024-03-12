
from contacts.schema.types.types import SupplierType, InvoiceAddressType, ShippingAddressType
from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field

from typing import List

from currencies.schema.types.types import CurrencyType
from products.schema.types.types import ProductVariationType
from purchasing.models import SupplierProduct, PurchaseOrder, \
    PurchaseOrderItem
from units.schema.types.types import UnitType
from .filters import SupplierProductFilter, PurchaseOrderFilter, \
    PurchaseOrderItemFilter
from .ordering import SupplierProductOrder, PurchaseOrderOrder, \
    PurchaseOrderItemOrder


@type(SupplierProduct, filters=SupplierProductFilter, order=SupplierProductOrder, pagination=True, fields="__all__")
class SupplierProductType(relay.Node, GetQuerysetMultiTenantMixin):
    supplier: SupplierType
    product: ProductVariationType
    unit: UnitType
    currency: CurrencyType


@type(PurchaseOrder, filters=PurchaseOrderFilter, order=PurchaseOrderOrder, pagination=True, fields="__all__")
class PurchaseOrderType(relay.Node, GetQuerysetMultiTenantMixin):
    supplier: SupplierType
    currency: CurrencyType
    invoice_address: InvoiceAddressType
    shipping_address: ShippingAddressType

    @field()
    def total_value(self) -> str | None:
        return self.total_value


@type(PurchaseOrderItem, filters=PurchaseOrderItemFilter, order=PurchaseOrderItemOrder, pagination=True, fields="__all__")
class PurchaseOrderItemType(relay.Node, GetQuerysetMultiTenantMixin):
    purchase_order: PurchaseOrderType
    item: SupplierProductType
