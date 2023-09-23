from core.schema.types.types import auto
from core.schema.types.filters import filter

from inventory.models import Inventory, InventoryLocation
from products.schema.types.filters import ProductVariationFilter


@filter(Inventory)
class InventoryFilter:
    id: auto
    location: 'InventoryLocationFilter'
    product: ProductVariationFilter


@filter(InventoryLocation)
class InventoryLocationFilter:
    id: auto
    name: auto
    parent_location: 'InventoryLocationFilter'
