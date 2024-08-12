from core.schema.core.mutations import create, update, delete, type, List, field

from .types.types import ShipmentType, PackageType, PackageItemType
from .types.input import ShipmentInput, ShipmentPartialInput, \
    PackageInput, PackagePartialInput, \
    PackageItemInput, PackageItemPartialInput


@type(name="Mutation")
class ShipmentsMutation:
    create_shipment: ShipmentType = create(ShipmentInput)
    create_shipments: List[ShipmentType] = create(ShipmentInput)
    update_shipment: ShipmentType = update(ShipmentPartialInput)
    delete_shipment: ShipmentType = delete()
    delete_shipments: List[ShipmentType] = delete()

    create_package: PackageType = create(PackageInput)
    create_packages: List[PackageType] = create(PackageInput)
    update_package: PackageType = update(PackagePartialInput)
    delete_package: PackageType = delete()
    delete_packages: List[PackageType] = delete()

    create_packageitem: PackageItemType = create(PackageItemInput)
    create_packageitems: List[PackageItemType] = create(PackageItemInput)
    update_packageitem: PackageItemType = update(PackageItemPartialInput)
    delete_packageitem: PackageItemType = delete()
    delete_packageitems: List[PackageItemType] = delete()
