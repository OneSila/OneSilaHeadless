
from contacts.schema.types.types import CompanyType, InvoiceAddressType, ShippingAddressType
from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field, lazy, Annotated

from typing import List

from currencies.schema.types.types import CurrencyType
from products.schema.types.types import SupplierProductType
from purchasing.models import PurchaseOrder, PurchaseOrderItem
from .filters import PurchaseOrderFilter, PurchaseOrderItemFilter
from .ordering import PurchaseOrderOrder, PurchaseOrderItemOrder


@type(PurchaseOrder, filters=PurchaseOrderFilter, order=PurchaseOrderOrder, pagination=True, fields="__all__")
class PurchaseOrderType(relay.Node, GetQuerysetMultiTenantMixin):
    supplier: CompanyType
    currency: CurrencyType
    invoice_address: InvoiceAddressType
    shipping_address: ShippingAddressType
    purchaseorderitem_set: List[Annotated['PurchaseOrderItemType', lazy("purchasing.schema.types.types")]]

    @field()
    def total_value(self) -> str | None:
        return self.total_value

    @field()
    def country(self, info) -> str | None:
        try:
            return self.invoice_address.get_country_display()
        except Exception:
            return None


@type(PurchaseOrderItem, filters=PurchaseOrderItemFilter, order=PurchaseOrderItemOrder, pagination=True, fields="__all__")
class PurchaseOrderItemType(relay.Node, GetQuerysetMultiTenantMixin):
    purchase_order: PurchaseOrderType
    item: SupplierProductType
