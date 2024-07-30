from typing import Self, Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, ExcluideDemoDataFilterMixin

from inventory.models import Inventory, InventoryLocation
from products.schema.types.filters import SupplierProductFilter
from contacts.schema.types.filters import InternalShippingAddressFilter


@filter(InventoryLocation)
class InventoryLocationFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    search: str | None
    exclude_demo_data: Optional[bool]
    id: auto
    name: auto
    shippingaddress: Optional[InternalShippingAddressFilter]


@filter(Inventory)
class InventoryFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    search: str | None
    exclude_demo_data: Optional[bool]
    id: auto
    inventorylocation: InventoryLocationFilter | None
    product: SupplierProductFilter | None
