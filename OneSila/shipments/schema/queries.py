from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import ShipmentType, PackageType, PackageItemType, ShipmentItemType, ShipmentItemToShipType


@type(name="Query")
class ShipmentsQuery:
    shipment: ShipmentType = node()
    shipments: ListConnectionWithTotalCount[ShipmentType] = connection()

    package: PackageType = node()
    packages: ListConnectionWithTotalCount[PackageType] = connection()

    packageitem: PackageItemType = node()
    packageitems: ListConnectionWithTotalCount[PackageItemType] = connection()

    shipmentitem: ShipmentItemType = node()
    shipmentitems: ListConnectionWithTotalCount[ShipmentItemType] = connection()

    shipmentitemtoship: ShipmentItemToShipType = node()
    shipmentitemstoship: ListConnectionWithTotalCount[ShipmentItemToShipType] = connection()
