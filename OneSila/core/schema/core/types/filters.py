from strawberry_django.filters import filter as strawberry_filter
from strawberry import UNSET


class SearchFilterMixin:
    search: str | None

    def filter_search(self, queryset):
        if self.search not in (None, UNSET):
            queryset = queryset.search(self.search)

        return queryset


def filter(*args, lookups=True, **kwargs):
    return strawberry_filter(*args, **kwargs, lookups=lookups)
