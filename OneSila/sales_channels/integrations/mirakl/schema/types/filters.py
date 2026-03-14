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
    MiraklProductCategory,
    MiraklProductContent,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklRemoteCurrency,
    MiraklRemoteLanguage,
    MiraklSalesChannel,
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
    required: auto
    variant: auto
    type: auto
    is_common: auto
    representation_type: auto

    def get_mapped_locally_querysets(self):
        return (
            (MiraklPropertyQuerySet, "filter_mapped_locally"),
            (MiraklPropertySelectValueQuerySet, "filter_mirakl_property_mapped_locally"),
        )


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
