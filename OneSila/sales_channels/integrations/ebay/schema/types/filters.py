from typing import Optional

from core.schema.core.types.filters import filter, SearchFilterMixin
from core.schema.core.types.types import auto
from sales_channels.integrations.ebay.models import (
    EbayCategory,
    EbayProductCategory,
    EbaySalesChannel,
    EbayInternalProperty,
    EbayInternalPropertyOption,
    EbayProductType,
    EbayProductTypeItem,
    EbayProperty,
    EbayPropertySelectValue,
    EbaySalesChannelImport,
    EbaySalesChannelView,
    EbayCurrency,
)
from currencies.schema.types.filters import CurrencyFilter
from properties.schema.types.filters import (
    ProductPropertiesRuleFilter,
    ProductPropertiesRuleItemFilter,
    PropertyFilter,
    PropertySelectValueFilter,
)
from products.schema.types.filters import ProductFilter
from sales_channels.schema.types.filters import SalesChannelFilter, SalesChannelViewFilter
from sales_channels.integrations.ebay.managers import (
    EbayPropertyQuerySet,
    EbayPropertySelectValueQuerySet, EbayInternalPropertyQuerySet,
)
from sales_channels.schema.types.filter_mixins import (
    DependentMappedLocallyFilterMixin,
    GeneralMappedLocallyFilterMixin,
    GeneralMappedRemotelyFilterMixin,
    DependentUsedInProductsFilterMixin,
    GeneralUsedInProductsFilterMixin,
)


@filter(EbaySalesChannel)
class EbaySalesChannelFilter(SearchFilterMixin):
    active: auto
    hostname: auto


@filter(EbayCategory)
class EbayCategoryFilter(SearchFilterMixin):
    id: auto
    marketplace_default_tree_id: auto
    remote_id: auto
    name: auto
    full_name: auto
    has_children: auto
    is_root: auto
    parent_node: Optional['EbayCategoryFilter']


@filter(EbayProductCategory)
class EbayProductCategoryFilter(SearchFilterMixin):
    id: auto
    product: Optional[ProductFilter]
    sales_channel: Optional[SalesChannelFilter]
    view: Optional[SalesChannelViewFilter]
    remote_id: auto


@filter(EbayProductType)
class EbayProductTypeFilter(SearchFilterMixin, GeneralMappedLocallyFilterMixin, GeneralMappedRemotelyFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[ProductPropertiesRuleFilter]
    marketplace: Optional[SalesChannelViewFilter]
    imported: auto


@filter(EbayProductTypeItem)
class EbayProductTypeItemFilter(SearchFilterMixin):
    id: auto
    product_type: Optional[EbayProductTypeFilter]
    local_instance: Optional[ProductPropertiesRuleItemFilter]
    ebay_property: Optional['EbayPropertyFilter']
    remote_type: auto


@filter(EbayProperty)
class EbayPropertyFilter(
    SearchFilterMixin,
    DependentMappedLocallyFilterMixin,
    DependentUsedInProductsFilterMixin,
    GeneralMappedRemotelyFilterMixin,
):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[PropertyFilter]
    allows_unmapped_values: auto
    type: auto

    def get_mapped_locally_querysets(self):
        return (
            (EbayPropertyQuerySet, "filter_mapped_locally"),
            (EbayPropertySelectValueQuerySet, "filter_ebay_property_mapped_locally"),
        )

    def get_used_in_products_querysets(self):
        return (
            (EbayPropertyQuerySet, "used_in_products"),
            (EbayPropertySelectValueQuerySet, "filter_ebay_property_used_in_products"),
        )


@filter(EbayInternalProperty)
class EbayInternalPropertyFilter(SearchFilterMixin, DependentMappedLocallyFilterMixin, GeneralMappedRemotelyFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[PropertyFilter]
    code: auto
    is_root: auto

    def get_mapped_locally_querysets(self):
        return (
            (EbayInternalPropertyQuerySet, "filter_mapped_locally"),
            (EbayPropertySelectValueQuerySet, "filter_ebay_property_mapped_locally"),
        )


@filter(EbayInternalPropertyOption)
class EbayInternalPropertyOptionFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    internal_property: Optional[EbayInternalPropertyFilter]
    value: auto
    is_active: auto
    local_instance: Optional[PropertySelectValueFilter]


@filter(EbayPropertySelectValue)
class EbayPropertySelectValueFilter(
    SearchFilterMixin,
    GeneralUsedInProductsFilterMixin,
    GeneralMappedLocallyFilterMixin,
    GeneralMappedRemotelyFilterMixin,
):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    ebay_property: Optional[EbayPropertyFilter]
    local_instance: Optional[PropertySelectValueFilter]
    marketplace: Optional[SalesChannelViewFilter]


@filter(EbaySalesChannelView)
class EbaySalesChannelViewFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    is_default: auto


@filter(EbaySalesChannelImport)
class EbaySalesChannelImportFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    status: auto
    type: auto


@filter(EbayCurrency)
class EbayCurrencyFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    sales_channel_view: Optional[SalesChannelViewFilter]
    local_instance: Optional[CurrencyFilter]
