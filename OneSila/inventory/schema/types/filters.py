from typing import Self

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from inventory.models import Inventory, InventoryLocation
from products.schema.types.filters import SupplierProductFilter
from contacts.schema.types.filters import InternalShippingAddressFilter


@filter(InventoryLocation)
class InventoryLocationFilter(SearchFilterMixin):
    search: str | None
    id: auto
    name: auto
    location: InternalShippingAddressFilter


@filter(Inventory)
class InventoryFilter(SearchFilterMixin):
    search: str | None
    id: auto
    stocklocation: InventoryLocationFilter | None
    product: SupplierProductFilter | None
