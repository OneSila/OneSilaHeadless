from typing import Optional

from core.schema.core.types.filters import filter, ExcluideDemoDataFilterMixin, lazy
from products.schema.types.filters import ProductFilter
from products_inspector.models import Inspector, InspectorBlock
from core.schema.core.types.types import auto


@filter(Inspector)
class InspectorFilter(ExcluideDemoDataFilterMixin):
    id: auto
    has_missing_information: auto
    has_missing_optional_information: auto
    product: ProductFilter | None
    blocks: Optional[lazy['InspectorBlockFilter', "products_inspector.schema.types.filters"]]


@filter(InspectorBlock)
class InspectorBlockFilter:
    id: auto
    inspector: Optional[InspectorFilter]
    error_code: auto
    successfully_checked: auto
