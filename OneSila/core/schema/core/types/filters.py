from typing import Optional

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.db.models import Q
from django.utils.dateparse import parse_date
from strawberry_django.filters import filter_type as strawberry_filter
from strawberry_django import filter_field as custom_filter
from strawberry import UNSET
from strawberry import LazyType as lazy
from core.managers import QuerySet


class AnnotationMergerMixin:

    # this will merge type annotations like
    # search: Optional[str] from subclass to the main class so we don't need to declare it in every filter
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        annotations = {}
        for base in reversed(cls.__bases__):
            annotations.update(getattr(base, '__annotations__', {}))
        annotations.update(cls.__annotations__)
        cls.__annotations__ = annotations


class SearchFilterMixin(AnnotationMergerMixin):
    search: Optional[str]

    @custom_filter
    def search(
        self,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:

        if value not in (None, UNSET):
            queryset = queryset.search(value)

        return queryset, Q()


class ExcluideDemoDataFilterMixin(AnnotationMergerMixin):
    exclude_demo_data: Optional[bool]

    @custom_filter
    def exclude_demo_data(
        self,
        queryset: QuerySet,
        value: bool,
        prefix: str
    ) -> tuple[QuerySet, Q]:

        if value:
            from django.contrib.contenttypes.models import ContentType
            from core.models import DemoDataRelation

            supplier_content_type = ContentType.objects.get_for_model(queryset.model)
            queryset = queryset.exclude(
                id__in=DemoDataRelation.objects.filter(
                    content_type=supplier_content_type
                ).values("object_id")
            )

        return queryset, Q()


class TimeStampRangeFilterMixin(AnnotationMergerMixin):
    created_at_range: Optional[str]
    updated_at_range: Optional[str]

    @custom_filter
    def created_at_range(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        try:
            start_value, end_value = [item.strip() for item in value.split(",", 1)]
        except ValueError:
            return queryset, Q()

        start_date = None if start_value in ("", "None") else parse_date(start_value)
        end_date = None if end_value in ("", "None") else parse_date(end_value)

        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        return queryset, Q()

    @custom_filter
    def updated_at_range(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        try:
            start_value, end_value = [item.strip() for item in value.split(",", 1)]
        except ValueError:
            return queryset, Q()

        start_date = None if start_value in ("", "None") else parse_date(start_value)
        end_date = None if end_value in ("", "None") else parse_date(end_value)

        if start_date:
            queryset = queryset.filter(updated_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(updated_at__date__lte=end_date)

        return queryset, Q()


def filter(*args, lookups=True, **kwargs):
    return strawberry_filter(*args, **kwargs, lookups=lookups)
