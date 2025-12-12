from __future__ import annotations

from typing import Iterable, Optional

from core.managers import QuerySet
from django.db.models import Q
from strawberry import UNSET
from strawberry_django import filter_field as custom_filter

from core.schema.core.types.filters import AnnotationMergerMixin


class DependentMappedLocallyFilterMixin(AnnotationMergerMixin):
    mapped_locally: Optional[bool]

    def get_mapped_locally_querysets(self) -> Iterable[tuple[type[QuerySet], str]]:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_mapped_locally_querysets()",
        )

    @custom_filter
    def mapped_locally(self, queryset, value: bool, prefix: str) -> tuple[QuerySet, Q]:

        if value not in (None, UNSET):
            for queryset_class, method_name in self.get_mapped_locally_querysets():
                if isinstance(queryset, queryset_class):
                    queryset = getattr(queryset, method_name)(value)
                    break
            else:
                raise Exception(f"Unexpected queryset class: {type(queryset)}")

        return queryset, Q()


class GeneralMappedRemotelyFilterMixin(AnnotationMergerMixin):
    mapped_remotely: Optional[bool]

    @custom_filter
    def mapped_remotely(self, queryset, value: bool, prefix: str) -> tuple[QuerySet, Q]:
        if value not in (None, UNSET):
            queryset = queryset.filter_mapped_remotely(value)
        return queryset, Q()


class GeneralMappedLocallyFilterMixin(AnnotationMergerMixin):
    mapped_locally: Optional[bool]

    @custom_filter
    def mapped_locally(self, queryset, value: bool, prefix: str) -> tuple[QuerySet, Q]:
        if value not in (None, UNSET):
            queryset = queryset.filter_mapped_locally(value)
        return queryset, Q()


class DependentUsedInProductsFilterMixin(AnnotationMergerMixin):
    used_in_products: Optional[bool]

    def get_used_in_products_querysets(self) -> Iterable[tuple[type[QuerySet], str]]:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_used_in_products_querysets()",
        )

    @custom_filter
    def used_in_products(self, queryset, value: bool, prefix: str) -> tuple[QuerySet, Q]:
        if value not in (None, UNSET):
            for queryset_class, method_name in self.get_used_in_products_querysets():
                if isinstance(queryset, queryset_class):
                    queryset = getattr(queryset, method_name)(value)
                    break
            else:
                raise Exception(f"Unexpected queryset class: {type(queryset)}")

        return queryset, Q()


class GeneralUsedInProductsFilterMixin(AnnotationMergerMixin):
    used_in_products: Optional[bool]

    @custom_filter
    def used_in_products(self, queryset, value: bool, prefix: str) -> tuple[QuerySet, Q]:
        if value not in (None, UNSET):
            queryset = queryset.used_in_products(value)
        return queryset, Q()
