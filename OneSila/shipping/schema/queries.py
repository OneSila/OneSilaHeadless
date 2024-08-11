from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import ShipmentType, PackageType, PackageItemType


@type(name="Query")
class ShippingQuery:
    shipment: ShipmentType = node()
    shipments: ListConnectionWithTotalCount[ShipmentType] = connection()

    package: PackageType = node()
    packages: ListConnectionWithTotalCount[PackageType] = connection()

    packageitem: PackageItemType = node()
    packageitems: ListConnectionWithTotalCount[PackageItemType] = connection()
