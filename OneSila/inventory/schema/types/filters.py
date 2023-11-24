from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter

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
    # FIXME: Referencing self seems to crash the schema
    # parent_location: 'InventoryLocationFilter'
