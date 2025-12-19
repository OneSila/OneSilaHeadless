"""Filter definitions for Shein GraphQL types."""

from __future__ import annotations

from typing import Optional

from core.schema.core.types.filters import SearchFilterMixin, filter
from core.schema.core.types.types import auto
from currencies.schema.types.filters import CurrencyFilter
from sales_channels.integrations.shein.managers import (
    SheinInternalPropertyQuerySet,
    SheinPropertyQuerySet,
    SheinPropertySelectValueQuerySet,
)
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinInternalProperty,
    SheinInternalPropertyOption,
    SheinProductCategory,
    SheinProductIssue,
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
    DependentMappedLocallyFilterMixin, DependentUsedInProductsFilterMixin, GeneralUsedInProductsFilterMixin
from sales_channels.schema.types.filters import SalesChannelFilter, RemoteProductFilter
from properties.schema.types.filters import (
    ProductPropertiesRuleFilter,
    ProductPropertiesRuleItemFilter,
    PropertyFilter,
    PropertySelectValueFilter,
)
from products.schema.types.filters import ProductFilter


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
class SheinPropertyFilter(
    SearchFilterMixin,
    DependentMappedLocallyFilterMixin,
    DependentUsedInProductsFilterMixin,
    GeneralMappedRemotelyFilterMixin,
):
    """Filter Shein attribute definitions."""

    id: auto
    sales_channel: Optional[SalesChannelFilter]
    local_instance: Optional[PropertyFilter]
    allows_unmapped_values: auto
    value_mode: auto
    type: auto

    def get_mapped_locally_querysets(self):
        return (
            (SheinPropertyQuerySet, "filter_mapped_locally"),
            (SheinPropertySelectValueQuerySet, "filter_shein_property_mapped_locally"),
        )

    def get_used_in_products_querysets(self):
        return (
            (SheinPropertyQuerySet, "used_in_products"),
            (SheinPropertySelectValueQuerySet, "filter_shein_property_used_in_products"),
        )


@filter(SheinPropertySelectValue)
class SheinPropertySelectValueFilter(
    SearchFilterMixin,
    GeneralUsedInProductsFilterMixin,
    GeneralMappedLocallyFilterMixin,
    GeneralMappedRemotelyFilterMixin,
):
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

    def get_mapped_locally_querysets(self):
        return (
            (SheinInternalPropertyQuerySet, "filter_mapped_locally"),
        )


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


@filter(SheinProductCategory)
class SheinProductCategoryFilter(SearchFilterMixin):
    """Filter product-to-category mappings for Shein listings."""

    id: auto
    product: Optional[ProductFilter]
    sales_channel: Optional[SalesChannelFilter]
    remote_id: auto
    site_remote_id: auto


@filter(SheinProductIssue)
class SheinProductIssueFilter(SearchFilterMixin):
    """Filter Shein review/audit issues."""

    id: auto
    remote_product: Optional[RemoteProductFilter]
    version: auto
    document_sn: auto
    spu_name: auto
    skc_name: auto
    audit_state: auto
    document_state: auto
    is_active: auto
