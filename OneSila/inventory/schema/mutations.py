from core.schema.core.mutations import type
from core.schema.core.mutations import create, update, delete, type, List

from .types.types import InventoryType, InventoryLocationType, InventoryMovementType
from .types.input import InventoryInput, InventoryLocationInput, \
    InventoryPartialInput, InventoryLocationPartialInput, InventoryMovementInput, \
    InventoryMovementPartialInput


@type(name="Mutation")
class InventoryMutation:
    create_inventory: InventoryType = create(InventoryInput)
    create_inventories: List[InventoryType] = create(InventoryInput)
    update_inventory: InventoryType = update(InventoryPartialInput)
    delete_inventory: InventoryType = delete()
    delete_inventories: List[InventoryType] = delete()

    create_inventory_location: InventoryLocationType = create(InventoryLocationInput)
    create_inventory_locations: List[InventoryLocationType] = create(InventoryLocationInput)
    update_inventory_location: InventoryLocationType = update(InventoryLocationPartialInput)
    delete_inventory_location: InventoryLocationType = delete()
    delete_inventory_locations: List[InventoryLocationType] = delete()

    create_inventory_movement: InventoryMovementType = create(InventoryMovementInput)
    create_inventory_movements: List[InventoryMovementType] = create(InventoryMovementInput)
    update_inventory_movement: InventoryMovementType = update(InventoryMovementPartialInput)
    delete_inventory_movement: InventoryMovementType = delete()
    delete_inventory_movements: List[InventoryMovementType] = delete()

    # InventoryMovements are generic relations.
    # so we need a mutaton that can translate the a given type eg. PurchaseOrderType
    # into the right ContentType which can then be used to either set
    # the fields mt_content_type and mt_object_id which must also be given.
    # or the mutation can fetch the right object and set that as movement_to

    # eg payload:
    # data: {
    #     "mt_content_type": "PurchaseOrderType" <- Needs translating into real content-type
    #     "mt_object_id": "AJDJDH29292" <- GlobalId needs translting into the real id....actaully.
    # }

    # Looking through this. The globalid already gives you the right content-type implecitly when
    # decodding the string.
    # that means it may actually be possible to just set the correct items straight in the mutation if the type is
    # changable.
