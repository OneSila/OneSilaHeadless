from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from shipping.models import Shipment, Package, PackageItem


@order(Shipment)
class ShipmentOrder:
    pass


@order(Package)
class PackageOrder:
    pass


@order(PackageItem)
class PackageItemOrder:
    pass
