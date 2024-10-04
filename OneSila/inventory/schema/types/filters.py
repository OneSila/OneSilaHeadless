from typing import Self, Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, ExcluideDemoDataFilterMixin, lazy

from inventory.models import Inventory, InventoryLocation, InventoryMovement
from products.schema.types.filters import SupplierProductFilter, ProductFilter
from contacts.schema.types.filters import InventoryShippingAddressFilter


@filter(InventoryLocation)
class InventoryLocationFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    search: str | None
    exclude_demo_data: Optional[bool]
    id: auto
    name: auto
    shippingaddress: Optional[InventoryShippingAddressFilter]
    inventory: Optional[lazy['InventoryFilter', "inventory.schema.types.filters"]]


@filter(Inventory)
class InventoryFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    search: str | None
    exclude_demo_data: Optional[bool]
    id: auto
    quantity: auto
    inventorylocation: InventoryLocationFilter | None
    product: SupplierProductFilter | None

@filter(InventoryMovement)
class InventoryMovementFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    search: str | None
    product: ProductFilter | None