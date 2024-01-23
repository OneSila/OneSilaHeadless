from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from inventory.models import Inventory, InventoryLocation
from products.schema.types.filters import ProductVariationFilter


@filter(Inventory)
class InventoryFilter(SearchFilterMixin):
    search: str | None
    id: auto
    location: 'InventoryLocationFilter'
    product: ProductVariationFilter


@filter(InventoryLocation)
class InventoryLocationFilter(SearchFilterMixin):
    search: str | None
    id: auto
    name: auto
    # FIXME: Referencing self seems to crash the schema
    # parent_location: 'InventoryLocationFilter'
