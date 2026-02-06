from typing import Optional

from core.schema.core.types.filters import filter, ExcluideDemoDataFilterMixin, lazy
from strawberry_django import filter_field as custom_filter
from strawberry import UNSET
from django.db.models import Q
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

    @custom_filter
    def has_any_missing_information(
        self,
        queryset,
        value: bool,
        prefix: str,
    ):
        if value in (None, UNSET):
            return queryset, Q()

        if value:
            return queryset, (
                Q(**{f"{prefix}has_missing_information": True})
                | Q(**{f"{prefix}has_missing_optional_information": True})
            )

        return queryset, (
            Q(**{f"{prefix}has_missing_information": False})
            & Q(**{f"{prefix}has_missing_optional_information": False})
        )


@filter(InspectorBlock)
class InspectorBlockFilter:
    id: auto
    inspector: Optional[InspectorFilter]
    error_code: auto
    successfully_checked: auto
