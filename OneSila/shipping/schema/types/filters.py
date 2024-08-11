from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, ExcluideDemoDataFilterMixin
from shipping.models import Shipment, Package, PackageItem


@filter(Shipment)
class ShipmentFilter(SearchFilterMixin):
    pass


@filter(Package)
class PackageFilter(SearchFilterMixin):
    pass


@filter(PackageItem)
class PackageItemFilter(SearchFilterMixin):
    pass
