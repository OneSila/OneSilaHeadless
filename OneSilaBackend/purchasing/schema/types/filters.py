from core.schema.types.types import auto
from core.schema.types.filters import filter

from purchasing.models import SupplierProduct, PurchaseOrder, PurchaseOrderItem
from product.schema.types.filters import ProductFilter
from currencies.schema.types.filters import CurrencyFilter
from units.schema.types.filters import UnitFilter
from contacts.schema.types.filters import SupplierFilter, InvoiceAddressFilter, \
    ShippingAddressFilter


@filter(SupplierProduct)
class SupplierProductFilter:
    id: auto
    sku: auto
    name: auto
    currency: CurrencyFilter
    product: ProductFilter
    supplier: SupplierFilter
    unit: UnitFilter


@filter(PurchaseOrder)
class PurchaseOrderFilter:
    id: auto
    status: auto
    supplier: SupplierFilter
    order_reference: auto
    currency: CurrencyFilter
    invoice_address: InvoiceAddressFilter
    shipping_address: ShippingAddressFilter


@filter(PurchaseOrderItem)
class PurchaseOrderItemFilter:
    id: auto
    purchase_order: PurchaseOrderFilter
    item: SupplierProductFilter
