from typing import Optional

from contacts.schema.types.filters import ShippingAddressFilter
from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, ExcluideDemoDataFilterMixin
from orders.schema.types.filters import OrderFilter
from shipments.models import Shipment, Package, PackageItem, ShipmentItem, ShipmentItemToShip


@filter(Shipment)
class ShipmentFilter(SearchFilterMixin):
    id: auto
    order: auto
    status: auto
    from_address: Optional[ShippingAddressFilter]
    to_address: Optional[ShippingAddressFilter]
    order: Optional[OrderFilter]


@filter(Package)
class PackageFilter(SearchFilterMixin):
    id: auto
    shipment: auto
    type: auto
    status: auto
    shipment: Optional[ShipmentFilter]


@filter(PackageItem)
class PackageItemFilter(SearchFilterMixin):
    package: PackageFilter

@filter(ShipmentItem)
class ShipmentItemFilter(SearchFilterMixin):
    orderitem: auto
    product: auto
    quantity: auto


@filter(ShipmentItemToShip)
class ShipmentItemToShipFilter(SearchFilterMixin):
    product: auto
    quantity: auto
    shipment: Optional[ShipmentFilter]
    orderitem: auto