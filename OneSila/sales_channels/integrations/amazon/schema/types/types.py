from core.schema.core.types.types import (
    relay,
    type,
    GetQuerysetMultiTenantMixin,
    field,
    strawberry_type,
    Annotated,
    lazy,
)
from typing import Optional, List
from strawberry.relay import to_base64
from imports_exports.schema.queries import ImportType
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonProductType,
    AmazonProductTypeItem,
    AmazonSalesChannelImport,
    AmazonDefaultUnitConfigurator,
    AmazonRemoteLog,
)
from sales_channels.integrations.amazon.schema.types.filters import (
    AmazonSalesChannelFilter,
    AmazonPropertyFilter,
    AmazonPropertySelectValueFilter,
    AmazonProductTypeFilter,
    AmazonProductTypeItemFilter,
    AmazonSalesChannelImportFilter, AmazonDefaultUnitConfiguratorFilter,
    AmazonRemoteLogFilter,
)
from sales_channels.integrations.amazon.schema.types.ordering import (
    AmazonSalesChannelOrder,
    AmazonPropertyOrder,
    AmazonPropertySelectValueOrder,
    AmazonProductTypeOrder,
    AmazonProductTypeItemOrder,
    AmazonSalesChannelImportOrder,
    AmazonDefaultUnitConfiguratorOrder,
    AmazonRemoteLogOrder,
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


    @field(description="List of formatted issues coming from the remote marketplace")
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
                )
            )

        return formatted