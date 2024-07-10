from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, lazy, ExcluideDemoDataFilterMixin
from products.schema.types.filters import SupplierProductFilter

from purchasing.models import PurchaseOrder, PurchaseOrderItem
from currencies.schema.types.filters import CurrencyFilter
from contacts.schema.types.filters import SupplierFilter, InvoiceAddressFilter, \
    ShippingAddressFilter


@filter(PurchaseOrder)
class PurchaseOrderFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    search: str | None
    id: auto
    status: auto
    supplier: SupplierFilter | None
    order_reference: auto
    currency: CurrencyFilter | None
    invoice_address: InvoiceAddressFilter | None
    shipping_address: ShippingAddressFilter | None
    purchaseorderitem: Optional[lazy['PurchaseOrderItemFilter', "purchasing.schema.types.filters"]]
    exclude_demo_data: Optional[bool]


@filter(PurchaseOrderItem)
class PurchaseOrderItemFilter(SearchFilterMixin):
    search: str | None
    id: auto
    purchase_order: PurchaseOrderFilter | None
    item: SupplierProductFilter | None
