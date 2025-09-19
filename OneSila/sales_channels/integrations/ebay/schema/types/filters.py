from typing import Optional

from core.schema.core.types.filters import filter, SearchFilterMixin
from core.schema.core.types.types import auto
from sales_channels.integrations.ebay.models import (
    EbaySalesChannel,
    EbayInternalProperty,
    EbayProperty,
    EbayPropertySelectValue,
    EbaySalesChannelView,
)
from properties.schema.types.filters import PropertyFilter, PropertySelectValueFilter
from sales_channels.schema.types.filters import SalesChannelFilter, SalesChannelViewFilter
from sales_channels.integrations.ebay.managers import (
    EbayPropertyQuerySet,
    EbayPropertySelectValueQuerySet,
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


@filter(EbayProperty)
class EbayPropertyFilter(SearchFilterMixin, DependentMappedLocallyFilterMixin, GeneralMappedRemotelyFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[PropertyFilter]
    allows_unmapped_values: auto
    type: auto

    # mapped_locally_querysets = (
    #     (EbayPropertyQuerySet, "filter_mapped_locally"),
    #     (EbayPropertySelectValueQuerySet, "filter_ebay_property_mapped_locally"),
    # )


@filter(EbayInternalProperty)
class EbayInternalPropertyFilter(SearchFilterMixin, GeneralMappedLocallyFilterMixin, GeneralMappedRemotelyFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[PropertyFilter]
    code: auto
    is_root: auto


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
