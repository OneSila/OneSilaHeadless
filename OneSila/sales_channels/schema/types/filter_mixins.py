from __future__ import annotations

from typing import Iterable

from core.managers import QuerySet
from django.db.models import Q
from strawberry import UNSET
from strawberry_django import filter_field as custom_filter


class DependentMappedLocallyFilterMixin:
    mapped_locally_querysets: Iterable[tuple[type[QuerySet], str]] = ()

    @custom_filter
    def mapped_locally(self, queryset, value: bool, prefix: str) -> tuple[QuerySet, Q]:

        if value not in (None, UNSET):
            for queryset_class, method_name in self.mapped_locally_querysets:
                if isinstance(queryset, queryset_class):
                    queryset = getattr(queryset, method_name)(value)
                    break
            else:
                raise Exception(f"Unexpected queryset class: {type(queryset)}")

        return queryset, Q()


class GeneralMappedRemotelyFilterMixin:

    @custom_filter
    def mapped_remotely(self, queryset, value: bool, prefix: str) -> tuple[QuerySet, Q]:
        if value not in (None, UNSET):
            queryset = queryset.filter_mapped_remotely(value)
        return queryset, Q()


class GeneralMappedLocallyFilterMixin:

    @custom_filter
    def mapped_locally(self, queryset, value: bool, prefix: str) -> tuple[QuerySet, Q]:
        if value not in (None, UNSET):
            queryset = queryset.filter_mapped_locally(value)
        return queryset, Q()
