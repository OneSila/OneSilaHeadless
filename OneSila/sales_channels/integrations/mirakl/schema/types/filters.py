from typing import Optional

from core.schema.core.types.filters import SearchFilterMixin, filter, lazy
from core.schema.core.types.types import auto
from currencies.schema.types.filters import CurrencyFilter
from media.schema.types.filters import DocumentTypeFilter
from products.schema.types.filters import ProductFilter
from properties.schema.types.filters import PropertyFilter, PropertySelectValueFilter, ProductPropertiesRuleItemFilter
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklDocumentType,
    MiraklEanCode,
    MiraklInternalProperty,
    MiraklInternalPropertyOption,
    MiraklPrice,
    MiraklProduct,
    MiraklProductCategory,
    MiraklProductContent,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertyApplicability,
    MiraklPropertySelectValue,
    MiraklRemoteCurrency,
    MiraklRemoteLanguage,
    MiraklSalesChannel,
    MiraklSalesChannelImport,
    MiraklSalesChannelView,
)
from sales_channels.schema.types.filters import (
    RemoteProductContentFilter,
    RemoteProductFilter,
    SalesChannelFilter,
    SalesChannelImportFilter,
    SalesChannelViewFilter,
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


@filter(MiraklInternalProperty)
class MiraklInternalPropertyFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[PropertyFilter]
    code: auto
    is_condition: auto


@filter(MiraklInternalPropertyOption)
class MiraklInternalPropertyOptionFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    internal_property: Optional["MiraklInternalPropertyFilter"]
    local_instance: Optional[PropertySelectValueFilter]
    is_active: auto


@filter(MiraklCategory)
class MiraklCategoryFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    remote_id: auto
    name: auto
    parent: Optional["MiraklCategoryFilter"]
    is_leaf: auto


@filter(MiraklProperty)
class MiraklPropertyFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[PropertyFilter]
    code: auto
    required: auto
    variant: auto
    type: auto


@filter(MiraklPropertySelectValue)
class MiraklPropertySelectValueFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    remote_property: Optional["MiraklPropertyFilter"]
    local_instance: Optional[PropertySelectValueFilter]
    code: auto


@filter(MiraklPropertyApplicability)
class MiraklPropertyApplicabilityFilter(SearchFilterMixin):
    id: auto
    property: Optional["MiraklPropertyFilter"]
    view: Optional[SalesChannelViewFilter]


@filter(MiraklProductTypeItem)
class MiraklProductTypeItemFilter(SearchFilterMixin):
    id: auto
    category: Optional[MiraklCategoryFilter]
    property: Optional[MiraklPropertyFilter]
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


@filter(MiraklDocumentType)
class MiraklDocumentTypeFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[DocumentTypeFilter]


@filter(MiraklSalesChannelImport)
class MiraklSalesChannelImportFilter(SalesChannelImportFilter):
    type: auto
    remote_import_id: auto
    import_status: auto
