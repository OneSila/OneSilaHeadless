from typing import Self

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from inventory.models import Inventory, InventoryLocation
from products.schema.types.filters import ProductVariationFilter

@filter(InventoryLocation)
class InventoryLocationFilter(SearchFilterMixin):
    search: str | None
    id: auto
    name: auto
    parent_location: Self | None


@filter(Inventory)
class InventoryFilter(SearchFilterMixin):
    search: str | None
    id: auto
    location: InventoryLocationFilter | None
    product: ProductVariationFilter | None