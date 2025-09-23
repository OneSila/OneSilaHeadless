from typing import Optional

from core.schema.core.types.filters import filter, SearchFilterMixin
from core.schema.core.types.types import auto
from sales_channels.integrations.ebay.models import (
    EbaySalesChannel,
    EbayInternalProperty,
    EbayProductType,
    EbayProductTypeItem,
    EbayProperty,
    EbayPropertySelectValue,
    EbaySalesChannelView,
)
from properties.schema.types.filters import (
    ProductPropertiesRuleFilter,
    ProductPropertiesRuleItemFilter,
    PropertyFilter,
    PropertySelectValueFilter,
)
from sales_channels.schema.types.filters import SalesChannelFilter, SalesChannelViewFilter
from sales_channels.integrations.ebay.managers import (
    EbayPropertyQuerySet,
    EbayPropertySelectValueQuerySet, EbayInternalPropertyQuerySet,
)
from sales_channels.schema.types.filter_mixins import (
    DependentMappedLocallyFilterMixin,
    GeneralMappedLocallyFilterMixin,
    GeneralMappedRemotelyFilterMixin,
)


@filter(EbaySalesChannel)
class EbaySalesChannelFilter(SearchFilterMixin):
    active: auto
    hostname: auto


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
class EbayPropertyFilter(SearchFilterMixin, DependentMappedLocallyFilterMixin, GeneralMappedRemotelyFilterMixin):
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


@filter(EbayPropertySelectValue)
class EbayPropertySelectValueFilter(SearchFilterMixin, GeneralMappedLocallyFilterMixin, GeneralMappedRemotelyFilterMixin):
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
