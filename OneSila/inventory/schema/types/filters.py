from typing import Self, Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, ExcluideDemoDataFilterMixin, lazy

from inventory.models import Inventory, InventoryLocation, InventoryMovement
from products.schema.types.filters import SupplierProductFilter, ProductFilter
from contacts.schema.types.filters import InventoryShippingAddressFilter


@filter(InventoryLocation)
class InventoryLocationFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    name: auto
    shippingaddress: Optional[InventoryShippingAddressFilter]
    inventory: Optional[lazy['InventoryFilter', "inventory.schema.types.filters"]]


@filter(Inventory)
class InventoryFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    quantity: auto
    inventorylocation: InventoryLocationFilter | None
    product: SupplierProductFilter | None

@filter(InventoryMovement)
class InventoryMovementFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    product: ProductFilter | None