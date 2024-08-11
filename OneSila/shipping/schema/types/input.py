from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial, List

from shipping.models import Shipment, Package, PackageItem


@input(Shipment, fields="__all__")
class ShipmentInput:
    pass


@partial(Shipment, fields="__all__")
class ShipmentPartialInput(NodeInput):
    pass


@input(Package, fields="__all__")
class PackageInput:
    pass


@partial(Package, fields="__all__")
class PackagePartialInput(NodeInput):
    pass


@input(PackageItem, fields="__all__")
class PackageItemInput:
    pass


@partial(PackageItem, fields="__all__")
class PackageItemPartialInput(NodeInput):
    pass
