from typing import Optional

from core.schema.core.types.types import type, relay, List, Annotated, lazy, strawberry_type, field
from core.schema.core.mixins import GetQuerysetMultiTenantMixin
from core.schema.multi_tenant.types.types import MultiTenantCompanyType

from shipping.models import Shipment, Package, PackageItem
from .filters import ShipmentFilter, PackageFilter, PackageItemFilter
from .ordering import ShipmentOrder, PackageOrder, PackageItemOrder


@type(Shipment, filters=ShipmentFilter, order=ShipmentOrder, pagination=True, fields='__all__')
class ShipmentType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None


@type(Package, filters=PackageFilter, order=PackageOrder, pagination=True, fields='__all__')
class PackageType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    packageitem_set: List[Annotated['PackageItemType', lazy("shipments.schema.types.types")]]


@type(PackageItem, filters=PackageItemFilter, order=PackageItemOrder, pagination=True, fields='__all__')
class PackageItemType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
