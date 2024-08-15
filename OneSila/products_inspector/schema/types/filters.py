from core.schema.core.types.filters import filter, ExcluideDemoDataFilterMixin
from products.schema.types.filters import ProductFilter
from products_inspector.models import Inspector
from core.schema.core.types.types import auto


@filter(Inspector)
class InspectorFilter(ExcluideDemoDataFilterMixin):
    id: auto
    has_missing_information: auto
    has_missing_optional_information: auto
    product: ProductFilter | None
