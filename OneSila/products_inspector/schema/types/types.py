from core.schema.core.mixins import GetQuerysetMultiTenantMixin
from core.schema.core.types.types import field, relay, type, strawberry_type
from products_inspector.models import Inspector
from .filters import InspectorFilter
from .ordering import InspectorOrder
from typing import List


@strawberry_type
class InspectorErrorType:
    code: str


@type(Inspector, filters=InspectorFilter, order=InspectorOrder, pagination=True, fields="__all__")
class InspectorType(relay.Node, GetQuerysetMultiTenantMixin):

    @field()
    def errors(self, info) -> List[int] | None:
        return [block.error_code for block in self.blocks.filter(successfully_checked=False)]
