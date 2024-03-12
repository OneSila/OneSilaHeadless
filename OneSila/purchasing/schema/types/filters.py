from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from purchasing.models import SupplierProduct, PurchaseOrder, PurchaseOrderItem
from products.schema.types.filters import ProductFilter
from currencies.schema.types.filters import CurrencyFilter
from units.schema.types.filters import UnitFilter
from contacts.schema.types.filters import SupplierFilter, InvoiceAddressFilter, \
    ShippingAddressFilter


@filter(SupplierProduct)
class SupplierProductFilter(SearchFilterMixin):
    search: str | None
    id: auto
    sku: auto
    name: auto
    currency: CurrencyFilter | None
    product: ProductFilter | None
    supplier: SupplierFilter | None
    unit: UnitFilter | None


@filter(PurchaseOrder)
class PurchaseOrderFilter(SearchFilterMixin):
    search: str | None
    id: auto
    status: auto
    supplier: SupplierFilter | None
    order_reference: auto
    currency: CurrencyFilter | None
    invoice_address: InvoiceAddressFilter | None
    shipping_address: ShippingAddressFilter | None


@filter(PurchaseOrderItem)
class PurchaseOrderItemFilter(SearchFilterMixin):
    search: str | None
    id: auto
    purchase_order: PurchaseOrderFilter | None
    item: SupplierProductFilter | None
