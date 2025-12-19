"""Strawberry types for the Shein integration."""

from typing import Annotated, List, Optional

from core.schema.core.types.types import (
    GetQuerysetMultiTenantMixin,
    field,
    lazy,
    relay,
    strawberry_type,
    type,
)
from strawberry.scalars import JSON
from strawberry.relay import to_base64
from imports_exports.schema.queries import ImportType

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
from sales_channels.integrations.shein.schema.types.filters import (
    SheinCategoryFilter,
    SheinInternalPropertyFilter,
    SheinInternalPropertyOptionFilter,
    SheinProductCategoryFilter,
    SheinProductIssueFilter,
    SheinProductTypeFilter,
    SheinProductTypeItemFilter,
    SheinPropertyFilter,
    SheinPropertySelectValueFilter,
    SheinRemoteCurrencyFilter,
    SheinSalesChannelFilter,
    SheinSalesChannelViewFilter,
    SheinSalesChannelImportFilter,
)
from sales_channels.integrations.shein.schema.types.ordering import (
    SheinCategoryOrder,
    SheinInternalPropertyOptionOrder,
    SheinInternalPropertyOrder,
    SheinProductCategoryOrder,
    SheinProductIssueOrder,
    SheinProductTypeItemOrder,
    SheinProductTypeOrder,
    SheinPropertyOrder,
    SheinPropertySelectValueOrder,
    SheinRemoteCurrencyOrder,
    SheinSalesChannelOrder,
    SheinSalesChannelViewOrder,
    SheinSalesChannelImportOrder,
)


@strawberry_type
class SheinRedirectUrlType:
    """Container for the Shein authorization redirect link."""

    redirect_url: str


@strawberry_type
class SheinSalesChannelMappingSyncPayload:
    """Result payload for Shein mapping sync."""

    success: bool


@type(
    SheinCategory,
    filters=SheinCategoryFilter,
    order=SheinCategoryOrder,
    pagination=True,
    fields="__all__",
)
class SheinCategoryType(relay.Node):
    """Expose public Shein category metadata for lookups."""

    parent: Optional[Annotated[
        'SheinCategoryType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]]
    children: List[Annotated[
        'SheinCategoryType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]]

    @field(name="configuratorProperties")
    def configurator_properties_field(self, info) -> JSON:
        return self.configurator_properties


@type(
    SheinProductCategory,
    filters=SheinProductCategoryFilter,
    order=SheinProductCategoryOrder,
    pagination=True,
    fields="__all__",
)
class SheinProductCategoryType(relay.Node, GetQuerysetMultiTenantMixin):
    """Expose the selected Shein category per product and sales channel."""

    product: Annotated[
        'ProductType',
        lazy("products.schema.types.types")
    ]
    sales_channel: Annotated[
        'SheinSalesChannelType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]


@type(
    SheinProductIssue,
    filters=SheinProductIssueFilter,
    order=SheinProductIssueOrder,
    pagination=True,
    fields="__all__",
)
class SheinProductIssueType(relay.Node, GetQuerysetMultiTenantMixin):
    """Expose Shein review/audit issues for remote products."""

    remote_product: Annotated[
        "RemoteProductType",
        lazy("sales_channels.schema.types.types")
    ]


@type(
    SheinSalesChannel,
    filters=SheinSalesChannelFilter,
    order=SheinSalesChannelOrder,
    pagination=True,
    fields="__all__",
)
class SheinSalesChannelType(relay.Node, GetQuerysetMultiTenantMixin):
    """Expose Shein sales channel fields through GraphQL."""

    @field()
    def integration_ptr(self, info) -> str:
        return self.integration_ptr

    @field()
    def saleschannel_ptr(self, info) -> str:
        return self.saleschannel_ptr


@type(
    SheinSalesChannelView,
    filters=SheinSalesChannelViewFilter,
    order=SheinSalesChannelViewOrder,
    pagination=True,
    fields="__all__",
)
class SheinSalesChannelViewType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'SheinSalesChannelType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]

    @field()
    def active(self, info) -> Optional[bool]:
        return self.is_active


@type(
    SheinRemoteCurrency,
    filters=SheinRemoteCurrencyFilter,
    order=SheinRemoteCurrencyOrder,
    pagination=True,
    fields="__all__",
)
class SheinRemoteCurrencyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'SheinSalesChannelType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]
    local_instance: Optional[Annotated[
        'CurrencyType',
        lazy("currencies.schema.types.types")
    ]]

    @field()
    def proxy_id(self, info) -> str:
        from sales_channels.schema.types.types import RemoteCurrencyType

        return to_base64(RemoteCurrencyType, self.pk)


@type(
    SheinProperty,
    filters=SheinPropertyFilter,
    order=SheinPropertyOrder,
    pagination=True,
    fields="__all__",
)
class SheinPropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'SheinSalesChannelType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]
    local_instance: Optional[Annotated[
        'PropertyType',
        lazy("properties.schema.types.types")
    ]]
    select_values: List[Annotated[
        'SheinPropertySelectValueType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]]

    @field()
    def mapped_locally(self, info) -> bool:
        annotated_value = getattr(self, "mapped_locally", None)
        if annotated_value is None:
            return bool(getattr(self, "local_instance_id", None))
        return annotated_value

    @field()
    def mapped_remotely(self, info) -> bool:
        annotated_value = getattr(self, "mapped_remotely", None)
        if annotated_value is None:
            remote_id = getattr(self, "remote_id", None)
            return bool(remote_id)
        return annotated_value


@type(
    SheinPropertySelectValue,
    filters=SheinPropertySelectValueFilter,
    order=SheinPropertySelectValueOrder,
    pagination=True,
    fields="__all__",
    disable_optimization=True,
)
class SheinPropertySelectValueType(relay.Node, GetQuerysetMultiTenantMixin):
    remote_property: Annotated[
        'SheinPropertyType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]
    local_instance: Optional[Annotated[
        'PropertySelectValueType',
        lazy("properties.schema.types.types")
    ]]

    @field()
    def mapped_locally(self, info) -> bool:
        annotated_value = getattr(self, "mapped_locally", None)
        if annotated_value is None:
            return bool(getattr(self, "local_instance_id", None))
        return annotated_value

    @field()
    def mapped_remotely(self, info) -> bool:
        annotated_value = getattr(self, "mapped_remotely", None)
        if annotated_value is None:
            return bool(getattr(self, "remote_id", None))
        return annotated_value


@type(
    SheinSalesChannelImport,
    filters=SheinSalesChannelImportFilter,
    order=SheinSalesChannelImportOrder,
    pagination=True,
    fields="__all__",
)
class SheinSalesChannelImportType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'SheinSalesChannelType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]

    @field()
    def import_id(self, info) -> str:
        return to_base64(ImportType, self.pk)

    @field()
    def proxy_id(self, info) -> str:
        from sales_channels.schema.types.types import SalesChannelImportType

        return to_base64(SalesChannelImportType, self.pk)


@strawberry_type
class SuggestedSheinCategoryEntry:
    """Normalized Shein category suggestion entry."""

    category_id: str
    product_type_id: str
    category_name: str
    category_path: str
    leaf: bool
    order: Optional[int]
    vote: Optional[int]


@strawberry_type
class SuggestedSheinCategory:
    """Container for Shein category suggestion results."""

    site_remote_id: str
    categories: List[SuggestedSheinCategoryEntry]


@type(
    SheinProductType,
    filters=SheinProductTypeFilter,
    order=SheinProductTypeOrder,
    pagination=True,
    fields="__all__",
)
class SheinProductTypeType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'SheinSalesChannelType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]
    local_instance: Optional[Annotated[
        'ProductPropertiesRuleType',
        lazy("properties.schema.types.types")
    ]]
    items: List[Annotated[
        'SheinProductTypeItemType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]]

    @field()
    def mapped_locally(self, info) -> bool:
        annotated_value = getattr(self, "mapped_locally", None)
        if annotated_value is None:
            return bool(getattr(self, "local_instance_id", None))
        return annotated_value

    @field()
    def mapped_remotely(self, info) -> bool:
        annotated_value = getattr(self, "mapped_remotely", None)
        if annotated_value is None:
            remote_id = getattr(self, "remote_id", None)
            return bool(remote_id)
        return annotated_value


@type(
    SheinProductTypeItem,
    filters=SheinProductTypeItemFilter,
    order=SheinProductTypeItemOrder,
    pagination=True,
    fields="__all__",
)
class SheinProductTypeItemType(relay.Node, GetQuerysetMultiTenantMixin):
    product_type: Annotated[
        'SheinProductTypeType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]
    property: Annotated[
        'SheinPropertyType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]
    local_instance: Optional[Annotated[
        'ProductPropertiesRuleItemType',
        lazy("properties.schema.types.types")
    ]]


@type(
    SheinInternalProperty,
    filters=SheinInternalPropertyFilter,
    order=SheinInternalPropertyOrder,
    pagination=True,
    fields="__all__",
)
class SheinInternalPropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'SheinSalesChannelType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]
    local_instance: Optional[Annotated[
        'PropertyType',
        lazy("properties.schema.types.types")
    ]]
    options: List[Annotated[
        'SheinInternalPropertyOptionType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]]

    @field()
    def mapped_locally(self, info) -> bool:
        annotated_value = getattr(self, "mapped_locally", None)
        if annotated_value is None:
            return bool(getattr(self, "local_instance_id", None))
        return annotated_value

    @field()
    def mapped_remotely(self, info) -> bool:
        annotated_value = getattr(self, "mapped_remotely", None)
        if annotated_value is None:
            remote_id = getattr(self, "remote_id", None)
            return bool(remote_id)
        return annotated_value


@type(
    SheinInternalPropertyOption,
    filters=SheinInternalPropertyOptionFilter,
    order=SheinInternalPropertyOptionOrder,
    pagination=True,
    fields="__all__",
)
class SheinInternalPropertyOptionType(relay.Node, GetQuerysetMultiTenantMixin):
    internal_property: Annotated[
        'SheinInternalPropertyType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]
    sales_channel: Annotated[
        'SheinSalesChannelType',
        lazy("sales_channels.integrations.shein.schema.types.types")
    ]
    local_instance: Optional[Annotated[
        'PropertySelectValueType',
        lazy("properties.schema.types.types")
    ]]
