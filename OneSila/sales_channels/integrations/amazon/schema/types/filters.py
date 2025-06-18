from typing import Optional

from core.schema.core.types.filters import filter, SearchFilterMixin
from strawberry_django import filter_field as custom_filter
from django.db.models import Q
from strawberry import UNSET
from core.managers import QuerySet
from core.schema.core.types.types import auto
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonProductType,
)
from properties.schema.types.filters import (
    PropertyFilter,
    PropertySelectValueFilter,
    ProductPropertiesRuleFilter,
)
from sales_channels.schema.types.filters import (
    SalesChannelFilter,
    SalesChannelViewFilter,
)


@filter(AmazonSalesChannel)
class AmazonSalesChannelFilter(SearchFilterMixin):
    id: auto
    active: auto
    hostname: auto


@filter(AmazonProperty)
class AmazonPropertyFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[PropertyFilter]
    allows_unmapped_values: auto
    type: auto

    @custom_filter
    def mapped_locally(self, queryset, value: bool, prefix: str) -> tuple[QuerySet, Q]:
        if value not in (None, UNSET):
            queryset = queryset.filter_mapped_locally(value)
        return queryset, Q()

    @custom_filter
    def mapped_remotely(self, queryset, value: bool, prefix: str) -> tuple[QuerySet, Q]:
        if value not in (None, UNSET):
            queryset = queryset.filter_mapped_remotely(value)
        return queryset, Q()


@filter(AmazonPropertySelectValue)
class AmazonPropertySelectValueFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    amazon_property: Optional[AmazonPropertyFilter]
    local_instance: Optional[PropertySelectValueFilter]
    marketplace: Optional[SalesChannelViewFilter]

    @custom_filter
    def mapped_locally(self, queryset, value: bool, prefix: str) -> tuple[QuerySet, Q]:
        if value not in (None, UNSET):
            queryset = queryset.filter_mapped_locally(value)
        return queryset, Q()

    @custom_filter
    def mapped_remotely(self, queryset, value: bool, prefix: str) -> tuple[QuerySet, Q]:
        if value not in (None, UNSET):
            queryset = queryset.filter_mapped_remotely(value)
        return queryset, Q()


@filter(AmazonProductType)
class AmazonProductTypeFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[ProductPropertiesRuleFilter]

    @custom_filter
    def mapped_locally(self, queryset, value: bool, prefix: str) -> tuple[QuerySet, Q]:
        if value not in (None, UNSET):
            queryset = queryset.filter_mapped_locally(value)
        return queryset, Q()

    @custom_filter
    def mapped_remotely(self, queryset, value: bool, prefix: str) -> tuple[QuerySet, Q]:
        if value not in (None, UNSET):
            queryset = queryset.filter_mapped_remotely(value)
        return queryset, Q()
