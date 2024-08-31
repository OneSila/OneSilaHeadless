from typing import Optional

from strawberry_django.filters import filter as strawberry_filter
from strawberry import UNSET
from strawberry import LazyType as lazy

class SearchFilterMixin:
    search: str | None

    def filter_search(self, queryset) -> str | None:
        if self.search not in (None, UNSET):
            queryset = queryset.search(self.search)

        return queryset


class ExcluideDemoDataFilterMixin:
    exclude_demo_data: Optional[bool]
    def filter_exclude_demo_data(self, queryset):
        from django.contrib.contenttypes.models import ContentType
        from core.models import DemoDataRelation

        if self.exclude_demo_data:
            supplier_content_type = ContentType.objects.get_for_model(queryset.model)
            queryset = queryset.exclude(
                id__in=DemoDataRelation.objects.filter(
                    content_type=supplier_content_type
                ).values('object_id')
            )

        return queryset

def filter(*args, lookups=True, **kwargs):
    return strawberry_filter(*args, **kwargs, lookups=lookups)
