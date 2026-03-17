from typing import Optional

from core.schema.core.types.filters import SearchFilterMixin, filter, lazy
from core.schema.core.types.types import auto
from django.db.models import Q
from currencies.schema.types.filters import CurrencyFilter
from products.schema.types.filters import ProductFilter
from properties.schema.types.filters import PropertyFilter, PropertySelectValueFilter, ProductPropertiesRuleFilter, ProductPropertiesRuleItemFilter
from strawberry import UNSET
from strawberry_django import filter_field as custom_filter
from sales_channels.integrations.mirakl.managers import (
    MiraklPropertyQuerySet,
    MiraklPropertySelectValueQuerySet,
)
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklDocumentType,
    MiraklEanCode,
    MiraklPrice,
    MiraklProduct,
    MiraklProductIssue,
    MiraklProductCategory,
    MiraklProductContent,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklRemoteCurrency,
    MiraklRemoteLanguage,
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
    MiraklSalesChannelFeedItem,
    MiraklSalesChannelImport,
    MiraklSalesChannelView,
)
from sales_channels.schema.types.filter_mixins import DependentMappedLocallyFilterMixin, GeneralMappedLocallyFilterMixin, GeneralMappedRemotelyFilterMixin
from sales_channels.schema.types.filters import (
    RemoteProductContentFilter,
    RemoteProductFilter,
    SalesChannelFilter,
    SalesChannelImportFilter,
)


@filter(MiraklSalesChannel)
class MiraklSalesChannelFilter(SearchFilterMixin):
    id: auto
    active: auto
    hostname: auto
    sub_type: auto
    shop_id: auto


@filter(MiraklSalesChannelView)
class MiraklSalesChannelViewFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    remote_id: auto
    name: auto


@filter(MiraklRemoteCurrency)
class MiraklRemoteCurrencyFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[CurrencyFilter]
    remote_code: auto
    is_default: auto


@filter(MiraklRemoteLanguage)
class MiraklRemoteLanguageFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    remote_code: auto
    local_instance: auto
    is_default: auto


@filter(MiraklCategory)
class MiraklCategoryFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    remote_id: auto
    name: auto
    parent: Optional["MiraklCategoryFilter"]
    is_leaf: auto


@filter(MiraklDocumentType)
class MiraklDocumentTypeFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: auto
    remote_id: auto
    name: auto
    entity: auto


@filter(MiraklProductType)
class MiraklProductTypeFilter(
    SearchFilterMixin,
    GeneralMappedLocallyFilterMixin,
    GeneralMappedRemotelyFilterMixin,
):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    category: Optional[MiraklCategoryFilter]
    local_instance: Optional[ProductPropertiesRuleFilter]
    remote_id: auto
    name: auto
    ready_to_push: Optional[bool]

    @custom_filter
    def ready_to_push(self, queryset, value: bool, prefix: str):
        if value not in (None, UNSET):
            if value:
                queryset = queryset.exclude(template="")
                queryset = queryset.exclude(template__isnull=True)
            else:
                queryset = queryset.filter(Q(template="") | Q(template__isnull=True))
        return queryset, Q()


@filter(MiraklProperty)
class MiraklPropertyFilter(
    SearchFilterMixin,
    DependentMappedLocallyFilterMixin,
    GeneralMappedRemotelyFilterMixin,
):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[PropertyFilter]
    code: auto
    type: auto
    is_common: auto
    representation_type: auto
    show_property: Optional[bool]

    def get_mapped_locally_querysets(self):
        return (
            (MiraklPropertyQuerySet, "filter_mapped_locally"),
            (MiraklPropertySelectValueQuerySet, "filter_mirakl_property_mapped_locally"),
        )

    @custom_filter
    def show_property(self, queryset, value: bool, prefix: str):
        if value not in (None, UNSET) and value:
            queryset = queryset.filter(
                Q(representation_type_decided=False)
                | Q(
                    representation_type__in=[
                        MiraklProperty.REPRESENTATION_PROPERTY,
                        MiraklProperty.REPRESENTATION_CONDITION,
                    ]
                )
            )
        return queryset, Q()


@filter(MiraklPropertySelectValue)
class MiraklPropertySelectValueFilter(
    SearchFilterMixin,
    GeneralMappedLocallyFilterMixin,
    GeneralMappedRemotelyFilterMixin,
):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    remote_property: Optional["MiraklPropertyFilter"]
    local_instance: Optional[PropertySelectValueFilter]
    code: auto
    is_property_value: Optional[bool]

    @custom_filter
    def is_property_value(self, queryset, value: bool, prefix: str) -> tuple[MiraklPropertySelectValueQuerySet, Q]:
        if value not in (None, UNSET):
            queryset = queryset.filter_is_property_value(value)
        return queryset, Q()


@filter(MiraklProductTypeItem)
class MiraklProductTypeItemFilter(SearchFilterMixin):
    id: auto
    product_type: Optional[MiraklProductTypeFilter]
    remote_property: Optional[MiraklPropertyFilter]
    local_instance: Optional[ProductPropertiesRuleItemFilter]
    hierarchy_code: auto
    required: auto
    variant: auto
    requirement_level: auto


@filter(MiraklProductCategory)
class MiraklProductCategoryFilter(SearchFilterMixin):
    id: auto
    product: Optional[ProductFilter]
    sales_channel: Optional[SalesChannelFilter]
    remote_id: auto


@filter(MiraklProduct)
class MiraklProductFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[ProductFilter]
    remote_parent_product: Optional[RemoteProductFilter]


@filter(MiraklProductIssue)
class MiraklProductIssueFilter(SearchFilterMixin):
    id: auto
    remote_product: Optional[RemoteProductFilter]
    views: Optional[MiraklSalesChannelViewFilter]
    main_code: auto
    code: auto
    severity: auto
    reason_label: auto
    attribute_code: auto
    is_rejected: auto


@filter(MiraklSalesChannelFeed)
class MiraklSalesChannelFeedFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    type: auto
    stage: auto
    status: auto
    remote_id: auto
    import_status: auto
    product_type: Optional[MiraklProductTypeFilter]
    sales_channel_view: Optional[MiraklSalesChannelViewFilter]
    has_error_report: auto
    has_new_product_report: auto
    has_transformation_error_report: auto
    has_transformed_file: auto


@filter(MiraklSalesChannelFeedItem)
class MiraklSalesChannelFeedItemFilter(SearchFilterMixin):
    id: auto
    feed: Optional["MiraklSalesChannelFeedFilter"]
    remote_product: Optional[MiraklProductFilter]
    sales_channel_view: Optional[MiraklSalesChannelViewFilter]
    action: auto
    status: auto
    identifier: auto


@filter(MiraklProductContent)
class MiraklProductContentMiraklFilter(RemoteProductContentFilter):
    remote_product: Optional[RemoteProductFilter]


@filter(MiraklPrice)
class MiraklPriceFilter(SearchFilterMixin):
    id: auto
    remote_product: Optional[RemoteProductFilter]


@filter(MiraklEanCode)
class MiraklEanCodeFilter(SearchFilterMixin):
    id: auto
    remote_product: Optional[RemoteProductFilter]
    ean_code: auto


@filter(MiraklSalesChannelImport)
class MiraklSalesChannelImportFilter(SalesChannelImportFilter):
    type: auto
