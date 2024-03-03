from core.schema.core.types.types import type, relay, List, Annotated, lazy
from core.schema.core.mixins import GetQuerysetMultiTenantMixin

from customs.models import HsCode
from .filters import HsCodeFilter
from .ordering import HsCodeOrder


@type(HsCode, filters=HsCodeFilter, order=HsCodeOrder, pagination=True, fields='__all__')
class HsCodeType(relay.Node, GetQuerysetMultiTenantMixin):
    product: List[Annotated['ProductType', lazy("products.schema.types.types")]]
