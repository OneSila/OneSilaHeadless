import strawberry
from asgiref.sync import sync_to_async
from strawberry.relay import from_base64

from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from shipments.models import ShipmentItemToShip
from .types.types import InventoryType, InventoryLocationType, InventoryMovementType, PickingLocationType


@sync_to_async
def fetch_and_determine_picking_locations(db_id):
    # Fetch all required details and determine picking locations in one go
    item = ShipmentItemToShip.objects.select_related('product', 'shipment__from_address').get(id=db_id)
    product = item.product
    shipping_address = item.shipment.from_address

    # Determine the picking locations using the custom method
    picking_locations = product.inventory.determine_picking_locations(
        product, shipping_address, item.quantity
    )

    return [
        PickingLocationType(location=location.inventorylocation, quantity=quantity)
        for location, quantity in picking_locations.items()
    ]


async def get_picking_locations(info, item_to_ship_id: strawberry.ID) -> List[PickingLocationType]:
    # Decode the global ID to get the database ID
    _, db_id = from_base64(item_to_ship_id)

    # Fetch details and determine picking locations asynchronously
    picking_locations = await fetch_and_determine_picking_locations(db_id)

    # Convert the dictionary of locations and quantities to PickingLocationType
    return picking_locations



@type(name="Query")
class InventoryQuery:
    inventory: InventoryType = node()
    inventories: ListConnectionWithTotalCount[InventoryType] = connection()

    inventory_location: InventoryLocationType = node()
    inventory_locations: ListConnectionWithTotalCount[InventoryLocationType] = connection()

    inventory_movement: InventoryMovementType = node()
    inventory_movements: ListConnectionWithTotalCount[InventoryMovementType] = connection()

    picking_locations: List[PickingLocationType] = strawberry.field(resolver=get_picking_locations)
