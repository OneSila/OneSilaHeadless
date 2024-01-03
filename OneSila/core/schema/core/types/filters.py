from strawberry_django.filters import filter as strawberry_filter
from strawberry import UNSET


class SearchFilterMixin:
    search: str | None

    def filter_search(self, queryset) -> str | None:
        if self.search not in (None, UNSET):
            print(set(queryset.values_list('multi_tenant_company', flat=True)))
            queryset = queryset.search(self.search)

        return queryset


def filter(*args, lookups=True, **kwargs):
    return strawberry_filter(*args, **kwargs, lookups=lookups)
