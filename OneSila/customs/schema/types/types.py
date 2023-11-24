from core.schema.types.types import type, relay, List
from core.schema.mixins import GetQuerysetMultiTenantMixin

from customs.models import HsCode
from .filters import HsCodeFilter
from .ordering import HsCodeOrder


@type(HsCode, filters=HsCodeFilter, order=HsCodeOrder, pagination=True, fields='__all__')
class HsCodeType(relay.Node, GetQuerysetMultiTenantMixin):
    product = List['ProductType'] | None
