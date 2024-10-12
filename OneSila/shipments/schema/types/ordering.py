from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from shipments.models import Shipment, Package, PackageItem, ShipmentItemToShip, ShipmentItem


@order(Shipment)
class ShipmentOrder:
    id: auto


@order(Package)
class PackageOrder:
    id: auto
    type: auto
    status: auto


@order(PackageItem)
class PackageItemOrder:
    id: auto

@order(ShipmentItem)
class ShipmentItemOrder:
    id: auto

@order(ShipmentItemToShip)
class ShipmentItemToShipOrder:
    id: auto