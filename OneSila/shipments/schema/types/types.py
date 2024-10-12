from typing import Optional

from contacts.schema.types.types import ShippingAddressType
from core.schema.core.types.types import type, relay, List, Annotated, lazy, strawberry_type, field
from core.schema.core.mixins import GetQuerysetMultiTenantMixin
from core.schema.multi_tenant.types.types import MultiTenantCompanyType
from orders.schema.types.types import OrderType
from products.schema.types.types import ProductType

from shipments.models import Shipment, Package, PackageItem, ShipmentItem, ShipmentItemToShip
from .filters import ShipmentFilter, PackageFilter, PackageItemFilter, ShipmentItemFilter, ShipmentItemToShipFilter
from .ordering import ShipmentOrder, PackageOrder, PackageItemOrder, ShipmentItemOrder, ShipmentItemToShipOrder


@type(Shipment, filters=ShipmentFilter, order=ShipmentOrder, pagination=True, fields='__all__')
class ShipmentType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    from_address: ShippingAddressType
    to_address: ShippingAddressType
    order: OrderType

    @field()
    def reference(self) -> str | None:
        return self.reference

@type(Package, filters=PackageFilter, order=PackageOrder, pagination=True, fields='__all__')
class PackageType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    packageitem_set: List[Annotated['PackageItemType', lazy("shipments.schema.types.types")]]
    shipment: ShipmentType

@type(PackageItem, filters=PackageItemFilter, order=PackageItemOrder, pagination=True, fields='__all__')
class PackageItemType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    product: ProductType
    package: PackageType

@type(ShipmentItem, filters=ShipmentItemFilter, order=ShipmentItemOrder, pagination=True, fields='__all__')
class ShipmentItemType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None


@type(ShipmentItemToShip, filters=ShipmentItemToShipFilter, order=ShipmentItemToShipOrder, pagination=True, fields='__all__')
class ShipmentItemToShipType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    product: ProductType
    shipment: ShipmentType
    inventorylocation: Optional[Annotated['InventoryLocationType', lazy('inventory.schema.types.types')]]
