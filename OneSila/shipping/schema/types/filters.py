from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, ExcluideDemoDataFilterMixin
from shipping.models import Shipment, Package, PackageItem


@filter(Shipment)
class ShipmentFilter(SearchFilterMixin):
    order: auto
    from_address: auto
    to_address: auto


@filter(Package)
class PackageFilter(SearchFilterMixin):
    shipment: auto
    type: auto
    status: auto


@filter(PackageItem)
class PackageItemFilter(SearchFilterMixin):
    package: auto
