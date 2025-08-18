from typing import Optional

from core.schema.core.types.filters import filter, SearchFilterMixin
from strawberry_django import filter_field as custom_filter
from django.db.models import Q
from strawberry import UNSET
from core.managers import QuerySet
from core.schema.core.types.types import auto
from sales_channels.integrations.amazon.managers import AmazonPropertyQuerySet, AmazonPropertySelectValueQuerySet
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonProduct,
    AmazonProductProperty,
    AmazonProductType,
    AmazonSalesChannelImport,
    AmazonProductTypeItem,
    AmazonDefaultUnitConfigurator,
    AmazonRemoteLog,
    AmazonProductIssue,
    AmazonBrowseNode,
    AmazonProductBrowseNode,
    AmazonMerchantAsin,
    AmazonGtinExemption,
    AmazonVariationTheme,
)
from properties.schema.types.filters import (
    PropertyFilter,
    PropertySelectValueFilter,
    ProductPropertiesRuleFilter,
    ProductPropertiesRuleItemFilter,
    ProductPropertyFilter,
)
from products.schema.types.filters import ProductFilter
from sales_channels.schema.types.filters import (
    SalesChannelFilter,
    SalesChannelViewFilter,
    RemoteProductFilter,
)
from sales_channels.integrations.amazon.models import AmazonSalesChannelView


@filter(AmazonSalesChannel)
class AmazonSalesChannelFilter(SearchFilterMixin):
    id: auto
    active: auto
    hostname: auto


@filter(AmazonSalesChannelView)
class AmazonSalesChannelViewFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    is_default: auto


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
            if isinstance(queryset, AmazonPropertyQuerySet):
                queryset = queryset.filter_mapped_locally(value)
            elif isinstance(queryset, AmazonPropertySelectValueQuerySet):
                queryset = queryset.filter_amazon_property_mapped_locally(value)
            else:
                raise Exception(f"Unexpected queryset class: {type(queryset)}")

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


@filter(AmazonProductTypeItem)
class AmazonProductTypeItemFilter(SearchFilterMixin):
    id: auto
    amazon_rule: Optional[AmazonProductTypeFilter]
    local_instance: Optional[ProductPropertiesRuleItemFilter]
    remote_property: Optional[AmazonPropertyFilter]
    remote_type: auto


@filter(AmazonProduct)
class AmazonProductFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[ProductFilter]


@filter(AmazonProductProperty)
class AmazonProductPropertyFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[ProductPropertyFilter]
    remote_select_value: Optional[AmazonPropertySelectValueFilter]
    remote_product: Optional[AmazonProductFilter]


@filter(AmazonSalesChannelImport)
class AmazonSalesChannelImportFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    status: auto
    type: auto


@filter(AmazonDefaultUnitConfigurator)
class AmazonDefaultUnitConfiguratorFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    marketplace: Optional[SalesChannelViewFilter]

    @custom_filter
    def mapped_locally(self, queryset, value: bool, prefix: str) -> tuple[QuerySet, Q]:
        if value not in (None, UNSET):
            queryset = queryset.filter(selected_unit__isnull=not value)

        return queryset, Q()


@filter(AmazonRemoteLog)
class AmazonRemoteLogFilter(SearchFilterMixin):
    id: auto
    remote_product: Optional[RemoteProductFilter]


@filter(AmazonProductIssue)
class AmazonProductIssueFilter(SearchFilterMixin):
    id: auto
    view: Optional[SalesChannelViewFilter]
    remote_product: Optional[RemoteProductFilter]


@filter(AmazonBrowseNode)
class AmazonBrowseNodeFilter(SearchFilterMixin):
    remote_id: auto
    marketplace_id: auto
    name: auto
    context_name: auto
    path_depth: auto
    is_root: auto


@filter(AmazonProductBrowseNode)
class AmazonProductBrowseNodeFilter(SearchFilterMixin):
    id: auto
    product: Optional[ProductFilter]
    sales_channel: Optional[SalesChannelFilter]
    sales_channel_view: Optional[SalesChannelViewFilter]
    recommended_browse_node_id: auto


@filter(AmazonMerchantAsin)
class AmazonMerchantAsinFilter(SearchFilterMixin):
    id: auto
    product: Optional[ProductFilter]
    view: Optional[SalesChannelViewFilter]
    asin: auto


@filter(AmazonGtinExemption)
class AmazonGtinExemptionFilter(SearchFilterMixin):
    id: auto
    product: Optional[ProductFilter]
    view: Optional[SalesChannelViewFilter]
    value: auto


@filter(AmazonVariationTheme)
class AmazonVariationThemeFilter(SearchFilterMixin):
    id: auto
    product: Optional[ProductFilter]
    view: Optional[SalesChannelViewFilter]
    theme: auto
