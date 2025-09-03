from core.schema.core.types.types import (
    relay,
    type,
    GetQuerysetMultiTenantMixin,
    field,
    strawberry_type,
    Annotated,
    lazy,
)
from typing import Optional, List, Self
from strawberry.relay import to_base64
from imports_exports.schema.queries import ImportType
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonProduct,
    AmazonProductProperty,
    AmazonProductType,
    AmazonProductTypeItem,
    AmazonSalesChannelImport,
    AmazonDefaultUnitConfigurator,
    AmazonRemoteLog,
    AmazonSalesChannelView,
    AmazonProductIssue,
    AmazonBrowseNode,
    AmazonProductBrowseNode,
    AmazonExternalProductId,
    AmazonGtinExemption,
    AmazonVariationTheme,
    AmazonImportBrokenRecord,
)
from sales_channels.integrations.amazon.schema.types.filters import (
    AmazonSalesChannelFilter,
    AmazonPropertyFilter,
    AmazonPropertySelectValueFilter,
    AmazonProductFilter,
    AmazonProductPropertyFilter,
    AmazonProductTypeFilter,
    AmazonProductTypeItemFilter,
    AmazonSalesChannelImportFilter,
    AmazonDefaultUnitConfiguratorFilter,
    AmazonRemoteLogFilter,
    AmazonSalesChannelViewFilter,
    AmazonProductIssueFilter,
    AmazonBrowseNodeFilter,
    AmazonProductBrowseNodeFilter,
    AmazonExternalProductIdFilter,
    AmazonGtinExemptionFilter,
    AmazonVariationThemeFilter,
    AmazonImportBrokenRecordFilter,
)
from sales_channels.integrations.amazon.schema.types.ordering import (
    AmazonSalesChannelOrder,
    AmazonPropertyOrder,
    AmazonPropertySelectValueOrder,
    AmazonProductOrder,
    AmazonProductPropertyOrder,
    AmazonProductTypeOrder,
    AmazonProductTypeItemOrder,
    AmazonSalesChannelImportOrder,
    AmazonDefaultUnitConfiguratorOrder,
    AmazonRemoteLogOrder,
    AmazonSalesChannelViewOrder,
    AmazonProductIssueOrder,
    AmazonBrowseNodeOrder,
    AmazonProductBrowseNodeOrder,
    AmazonExternalProductIdOrder,
    AmazonGtinExemptionOrder,
    AmazonVariationThemeOrder,
    AmazonImportBrokenRecordOrder,
)
from sales_channels.schema.types.types import FormattedIssueType


@strawberry_type
class AmazonRedirectUrlType:
    redirect_url: str


@type(AmazonSalesChannel, filters=AmazonSalesChannelFilter, order=AmazonSalesChannelOrder, pagination=True, fields="__all__")
class AmazonSalesChannelType(relay.Node, GetQuerysetMultiTenantMixin):

    @field()
    def integration_ptr(self, info) -> str:
        return self.integration_ptr

    @field()
    def saleschannel_ptr(self, info) -> str:
        return self.saleschannel_ptr


@type(
    AmazonProperty,
    filters=AmazonPropertyFilter,
    order=AmazonPropertyOrder,
    pagination=True,
    fields="__all__",
)
class AmazonPropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'AmazonSalesChannelType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]
    local_instance: Optional[Annotated[
        'PropertyType',
        lazy("properties.schema.types.types")
    ]]
    select_values: List[Annotated[
        'AmazonPropertySelectValueType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]]

    @field()
    def mapped_locally(self, info) -> bool:
        return self.mapped_locally

    @field()
    def mapped_remotely(self, info) -> bool:
        return self.mapped_remotely


@type(
    AmazonPropertySelectValue,
    filters=AmazonPropertySelectValueFilter,
    order=AmazonPropertySelectValueOrder,
    pagination=True,
    fields="__all__",
)
class AmazonPropertySelectValueType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'AmazonSalesChannelType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]
    amazon_property: AmazonPropertyType
    marketplace: Annotated[
        'SalesChannelViewType',
        lazy("sales_channels.schema.types.types")
    ]
    local_instance: Optional[Annotated[
        'PropertySelectValueType',
        lazy("properties.schema.types.types")
    ]]

    @field()
    def mapped_locally(self, info) -> bool:
        return self.mapped_locally

    @field()
    def mapped_remotely(self, info) -> bool:
        return self.mapped_remotely


@type(
    AmazonProductType,
    filters=AmazonProductTypeFilter,
    order=AmazonProductTypeOrder,
    pagination=True,
    fields="__all__",
)
class AmazonProductTypeType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'AmazonSalesChannelType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]
    local_instance: Optional[Annotated[
        'ProductPropertiesRuleType',
        lazy("properties.schema.types.types")
    ]]
    amazonproducttypeitem_set: List[Annotated[
        'AmazonProductTypeItemType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]]

    @field()
    def mapped_locally(self, info) -> bool:
        return self.mapped_locally

    @field()
    def mapped_remotely(self, info) -> bool:
        return self.mapped_remotely


@type(
    AmazonSalesChannelImport,
    filters=AmazonSalesChannelImportFilter,
    order=AmazonSalesChannelImportOrder,
    pagination=True,
    fields="__all__",
)
class AmazonSalesChannelImportType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'AmazonSalesChannelType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]

    @field()
    def import_id(self, info) -> str:
        return to_base64(ImportType, self.pk)


@type(
    AmazonProductTypeItem,
    filters=AmazonProductTypeItemFilter,
    order=AmazonProductTypeItemOrder,
    pagination=True,
    fields="__all__",
)
class AmazonProductTypeItemType(relay.Node, GetQuerysetMultiTenantMixin):
    amazon_rule: Annotated[
        'AmazonProductTypeType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]
    remote_property: AmazonPropertyType
    local_instance: Optional[Annotated[
        'ProductPropertiesRuleItemType',
        lazy("properties.schema.types.types")
    ]]


@type(
    AmazonDefaultUnitConfigurator,
    filters=AmazonDefaultUnitConfiguratorFilter,
    order=AmazonDefaultUnitConfiguratorOrder,
    pagination=True,
    fields="__all__",
)
class AmazonDefaultUnitConfiguratorType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'AmazonSalesChannelType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]
    marketplace: Annotated[
        'SalesChannelViewType',
        lazy("sales_channels.schema.types.types")
    ]


@type(
    AmazonSalesChannelView,
    filters=AmazonSalesChannelViewFilter,
    order=AmazonSalesChannelViewOrder,
    pagination=True,
    fields="__all__",
)
class AmazonSalesChannelViewType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'AmazonSalesChannelType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]

    @field()
    def active(self, info) -> bool:
        return self.sales_channel.active


@type(
    AmazonProduct,
    filters=AmazonProductFilter,
    order=AmazonProductOrder,
    pagination=True,
    fields="__all__",
)
class AmazonProductType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'AmazonSalesChannelType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]
    local_instance: Optional[Annotated[
        'ProductType',
        lazy("products.schema.types.types")
    ]]
    issues: List[Annotated[
        'AmazonProductIssueType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]]

    @field()
    def has_errors(self, info) -> bool | None:
        return self.has_errors


@type(
    AmazonProductProperty,
    filters=AmazonProductPropertyFilter,
    order=AmazonProductPropertyOrder,
    pagination=True,
    fields="__all__",
)
class AmazonProductPropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'AmazonSalesChannelType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]
    local_instance: Optional[Annotated[
        'ProductPropertyType',
        lazy("properties.schema.types.types")
    ]]
    remote_product: Annotated[
        'AmazonProductType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]
    remote_select_value: Optional[Annotated[
        'AmazonPropertySelectValueType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]]
    remote_select_values: List[Annotated[
        'AmazonPropertySelectValueType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]]


@type(
    AmazonRemoteLog,
    filters=AmazonRemoteLogFilter,
    order=AmazonRemoteLogOrder,
    pagination=True,
    fields="__all__",
)
class AmazonRemoteLogType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'AmazonSalesChannelType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]

    @field()
    def type(self, info) -> str:
        return str(self.content_type)

    @field()
    def frontend_name(self, info) -> str:
        return self.frontend_name

    @field()
    def frontend_error(self, info) -> str | None:
        return self.frontend_error

    @field()
    def formatted_issues(self, info) -> List[FormattedIssueType]:
        issues_data = self.issues or []
        formatted: List[FormattedIssueType] = []

        for issue in issues_data:

            if not isinstance(issue, dict):
                continue

            formatted.append(
                FormattedIssueType(
                    message=issue.get("message"),
                    severity=issue.get("severity"),
                    validation_issue=issue.get("validation_issue", False),
                )
            )

        return formatted


@type(
    AmazonProductIssue,
    filters=AmazonProductIssueFilter,
    order=AmazonProductIssueOrder,
    pagination=True,
    fields="__all__",
)
class AmazonProductIssueType(relay.Node, GetQuerysetMultiTenantMixin):
    remote_product: Annotated[
        'RemoteProductType',
        lazy("sales_channels.schema.types.types")
    ]
    view: Annotated[
        'AmazonSalesChannelViewType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]


@type(
    AmazonBrowseNode,
    filters=AmazonBrowseNodeFilter,
    order=AmazonBrowseNodeOrder,
    pagination=True,
    fields="__all__",
)
class AmazonBrowseNodeType(relay.Node):
    parent_node: Self | None


@type(
    AmazonProductBrowseNode,
    filters=AmazonProductBrowseNodeFilter,
    order=AmazonProductBrowseNodeOrder,
    pagination=True,
    fields="__all__",
)
class AmazonProductBrowseNodeType(relay.Node, GetQuerysetMultiTenantMixin):
    product: Annotated[
        'ProductType',
        lazy("products.schema.types.types")
    ]
    sales_channel: Annotated[
        'AmazonSalesChannelType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]
    sales_channel_view: Annotated[
        'AmazonSalesChannelViewType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]


@type(
    AmazonExternalProductId,
    filters=AmazonExternalProductIdFilter,
    order=AmazonExternalProductIdOrder,
    pagination=True,
    fields="__all__",
)
class AmazonExternalProductIdType(relay.Node, GetQuerysetMultiTenantMixin):
    product: Annotated[
        'ProductType',
        lazy("products.schema.types.types")
    ]
    view: Annotated[
        'AmazonSalesChannelViewType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]


@type(
    AmazonGtinExemption,
    filters=AmazonGtinExemptionFilter,
    order=AmazonGtinExemptionOrder,
    pagination=True,
    fields="__all__",
)
class AmazonGtinExemptionType(relay.Node, GetQuerysetMultiTenantMixin):
    product: Annotated[
        'ProductType',
        lazy("products.schema.types.types")
    ]
    view: Annotated[
        'AmazonSalesChannelViewType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]


@type(
    AmazonVariationTheme,
    filters=AmazonVariationThemeFilter,
    order=AmazonVariationThemeOrder,
    pagination=True,
    fields="__all__",
)
class AmazonVariationThemeType(relay.Node, GetQuerysetMultiTenantMixin):
    product: Annotated[
        'ProductType',
        lazy("products.schema.types.types")
    ]
    view: Annotated[
        'AmazonSalesChannelViewType',
        lazy("sales_channels.integrations.amazon.schema.types.types")
    ]


@type(
    AmazonImportBrokenRecord,
    filters=AmazonImportBrokenRecordFilter,
    order=AmazonImportBrokenRecordOrder,
    pagination=True,
    fields="__all__",
)
class AmazonImportBrokenRecordType(relay.Node, GetQuerysetMultiTenantMixin):
    import_process: Annotated[
        'ImportType',
        lazy("imports_exports.schema.queries")
    ]


@strawberry_type
class SuggestedAmazonProductTypeEntry:
    display_name: str
    marketplace_ids: List[str]
    name: str


@strawberry_type
class SuggestedAmazonProductType:
    product_type_version: str
    product_types: List[SuggestedAmazonProductTypeEntry]
