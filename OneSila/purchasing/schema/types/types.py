from core.schema.types.types import relay, type, GetQuerysetMultiTenantMixin

from typing import List

from purchasing.models import SupplierProduct, PurchaseOrder, \
    PurchaseOrderItem
from .filters import SupplierProductFilter, PurchaseOrderFilter, \
    PurchaseOrderItemFilter
from .ordering import SupplierProductOrder, PurchaseOrderOrder, \
    PurchaseOrderItemOrder


@type(SupplierProduct, filters=SupplierProductFilter, order=SupplierProductOrder, pagination=True, fields="__all__")
class SupplierProductType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(PurchaseOrder, filters=PurchaseOrderFilter, order=PurchaseOrderOrder, pagination=True, fields="__all__")
class PurchaseOrderType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(PurchaseOrderItem, filters=PurchaseOrderItemFilter, order=PurchaseOrderItemOrder, pagination=True, fields="__all__")
class PurchaseOrderItemType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
