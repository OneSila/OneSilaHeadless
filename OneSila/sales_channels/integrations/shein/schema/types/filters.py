"""Filter definitions for Shein GraphQL types."""

from __future__ import annotations

from typing import Optional

from core.schema.core.types.filters import SearchFilterMixin, filter
from core.schema.core.types.types import auto
from currencies.schema.types.filters import CurrencyFilter
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinInternalProperty,
    SheinInternalPropertyOption,
    SheinProductType,
    SheinProductTypeItem,
    SheinProperty,
    SheinPropertySelectValue,
    SheinRemoteCurrency,
    SheinSalesChannel,
    SheinSalesChannelView,
    SheinSalesChannelImport,
)
from sales_channels.schema.types.filter_mixins import GeneralMappedLocallyFilterMixin, GeneralMappedRemotelyFilterMixin, \
    DependentMappedLocallyFilterMixin
from sales_channels.schema.types.filters import SalesChannelFilter
from properties.schema.types.filters import (
    ProductPropertiesRuleFilter,
    ProductPropertiesRuleItemFilter,
    PropertyFilter,
    PropertySelectValueFilter,
)


@filter(SheinSalesChannel)
class SheinSalesChannelFilter(SearchFilterMixin):
    """Filter Shein sales channels by basic attributes."""

    id: auto
    hostname: auto
    active: auto


@filter(SheinSalesChannelView)
class SheinSalesChannelViewFilter(SearchFilterMixin):
    """Filter Shein storefront mirrors."""

    id: auto
    sales_channel: Optional[SalesChannelFilter]
    is_default: auto
    store_type: auto
    site_status: auto


@filter(SheinSalesChannelImport)
class SheinSalesChannelImportFilter(SearchFilterMixin):
    """Filter Shein import processes."""

    id: auto
    sales_channel: Optional[SalesChannelFilter]
    status: auto
    type: auto


@filter(SheinRemoteCurrency)
class SheinRemoteCurrencyFilter(SearchFilterMixin):
    """Filter Shein remote currencies and their local mappings."""

    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[CurrencyFilter]
    remote_code: auto


@filter(SheinProperty)
class SheinPropertyFilter(SearchFilterMixin, DependentMappedLocallyFilterMixin, GeneralMappedRemotelyFilterMixin):
    """Filter Shein attribute definitions."""

    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[PropertyFilter]
    allows_unmapped_values: auto
    value_mode: auto
    type: auto


@filter(SheinPropertySelectValue)
class SheinPropertySelectValueFilter(SearchFilterMixin, GeneralMappedLocallyFilterMixin, GeneralMappedRemotelyFilterMixin):
    """Filter Shein enumeration values for an attribute."""

    id: auto
    sales_channel: Optional[SalesChannelFilter]
    remote_property: Optional[SheinPropertyFilter]
    local_instance: Optional[PropertySelectValueFilter]
    is_custom_value: auto
    is_visible: auto


@filter(SheinProductType)
class SheinProductTypeFilter(SearchFilterMixin, GeneralMappedLocallyFilterMixin, GeneralMappedRemotelyFilterMixin):
    """Filter Shein product type metadata."""

    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[ProductPropertiesRuleFilter]
    category_id: auto
    imported: auto


@filter(SheinProductTypeItem)
class SheinProductTypeItemFilter(SearchFilterMixin):
    """Filter mappings between product types and attributes."""

    id: auto
    product_type: Optional[SheinProductTypeFilter]
    property: Optional[SheinPropertyFilter]
    local_instance: Optional[ProductPropertiesRuleItemFilter]
    visibility: auto
    attribute_type: auto
    requirement: auto
    is_main_attribute: auto
    allows_unmapped_values: auto


@filter(SheinInternalProperty)
class SheinInternalPropertyFilter(SearchFilterMixin, DependentMappedLocallyFilterMixin, GeneralMappedRemotelyFilterMixin):
    """Filter static Shein payload fields."""

    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[PropertyFilter]
    code: auto
    is_root: auto
    type: auto


@filter(SheinInternalPropertyOption)
class SheinInternalPropertyOptionFilter(SearchFilterMixin):
    """Filter enumeration options for Shein internal fields."""

    id: auto
    sales_channel: Optional[SalesChannelFilter]
    internal_property: Optional[SheinInternalPropertyFilter]
    local_instance: Optional[PropertySelectValueFilter]
    value: auto
    is_active: auto


@filter(SheinCategory)
class SheinCategoryFilter(SearchFilterMixin):
    """Filter public Shein categories by the key attributes used in UIs."""

    id: auto
    remote_id: auto
    site_remote_id: auto
    parent_remote_id: auto
    product_type_remote_id: auto
    is_leaf: auto
    reference_info_required: auto
    parent: Optional['SheinCategoryFilter']
