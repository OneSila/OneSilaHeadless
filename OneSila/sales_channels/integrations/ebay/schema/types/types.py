from typing import Annotated, Optional, List

from core.schema.core.types.types import (
    relay,
    type,
    GetQuerysetMultiTenantMixin,
    strawberry_type,
    field,
    lazy,
)
from strawberry.relay import to_base64
from imports_exports.schema.queries import ImportType
from sales_channels.integrations.ebay.models import (
    EbaySalesChannel,
    EbayInternalProperty,
    EbayProductType,
    EbayProductTypeItem,
    EbayProperty,
    EbayPropertySelectValue,
    EbaySalesChannelImport,
    EbaySalesChannelView,
    EbayCurrency,
)
from sales_channels.integrations.ebay.schema.types.filters import (
    EbaySalesChannelFilter,
    EbayInternalPropertyFilter,
    EbayProductTypeFilter,
    EbayProductTypeItemFilter,
    EbayPropertyFilter,
    EbayPropertySelectValueFilter,
    EbaySalesChannelImportFilter,
    EbaySalesChannelViewFilter,
    EbayCurrencyFilter,
)
from sales_channels.integrations.ebay.schema.types.ordering import (
    EbaySalesChannelOrder,
    EbayInternalPropertyOrder,
    EbayProductTypeOrder,
    EbayProductTypeItemOrder,
    EbayPropertyOrder,
    EbayPropertySelectValueOrder,
    EbaySalesChannelImportOrder,
    EbaySalesChannelViewOrder,
    EbayCurrencyOrder,
)


@strawberry_type
class EbayRedirectUrlType:
    redirect_url: str


@type(EbaySalesChannel, filters=EbaySalesChannelFilter, order=EbaySalesChannelOrder, pagination=True, fields="__all__")
class EbaySalesChannelType(relay.Node, GetQuerysetMultiTenantMixin):

    @field()
    def integration_ptr(self, info) -> str:
        return self.integration_ptr

    @field()
    def saleschannel_ptr(self, info) -> str:
        return self.saleschannel_ptr


@type(
    EbayProductType,
    filters=EbayProductTypeFilter,
    order=EbayProductTypeOrder,
    pagination=True,
    fields="__all__",
)
class EbayProductTypeType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'EbaySalesChannelType',
        lazy("sales_channels.integrations.ebay.schema.types.types")
    ]
    local_instance: Optional[Annotated[
        'ProductPropertiesRuleType',
        lazy("properties.schema.types.types")
    ]]
    marketplace: Annotated[
        'SalesChannelViewType',
        lazy("sales_channels.schema.types.types")
    ]
    items: List[Annotated[
        'EbayProductTypeItemType',
        lazy("sales_channels.integrations.ebay.schema.types.types")
    ]]

    @field()
    def mapped_locally(self, info) -> bool:
        return self.mapped_locally

    @field()
    def mapped_remotely(self, info) -> bool:
        return self.mapped_remotely


@type(
    EbayProductTypeItem,
    filters=EbayProductTypeItemFilter,
    order=EbayProductTypeItemOrder,
    pagination=True,
    fields="__all__",
)
class EbayProductTypeItemType(relay.Node, GetQuerysetMultiTenantMixin):
    product_type: Annotated[
        'EbayProductTypeType',
        lazy("sales_channels.integrations.ebay.schema.types.types")
    ]
    ebay_property: Annotated[
        'EbayPropertyType',
        lazy("sales_channels.integrations.ebay.schema.types.types")
    ]
    local_instance: Optional[Annotated[
        'ProductPropertiesRuleItemType',
        lazy("properties.schema.types.types")
    ]]


@type(
    EbayProperty,
    filters=EbayPropertyFilter,
    order=EbayPropertyOrder,
    pagination=True,
    fields="__all__",
)
class EbayPropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'EbaySalesChannelType',
        lazy("sales_channels.integrations.ebay.schema.types.types")
    ]
    local_instance: Optional[Annotated[
        'PropertyType',
        lazy("properties.schema.types.types")
    ]]
    marketplace: Annotated[
        'SalesChannelViewType',
        lazy("sales_channels.schema.types.types")
    ]
    select_values: List[Annotated[
        'EbayPropertySelectValueType',
        lazy("sales_channels.integrations.ebay.schema.types.types")
    ]]

    @field()
    def mapped_locally(self, info) -> bool:
        return self.mapped_locally

    @field()
    def mapped_remotely(self, info) -> bool:
        return self.mapped_remotely


@type(
    EbayInternalProperty,
    filters=EbayInternalPropertyFilter,
    order=EbayInternalPropertyOrder,
    pagination=True,
    fields="__all__",
)
class EbayInternalPropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'EbaySalesChannelType',
        lazy("sales_channels.integrations.ebay.schema.types.types")
    ]
    local_instance: Optional[Annotated[
        'PropertyType',
        lazy("properties.schema.types.types")
    ]]

    @field()
    def mapped_locally(self, info) -> bool:
        return self.mapped_locally

    @field()
    def mapped_remotely(self, info) -> bool:
        return self.mapped_remotely


@type(
    EbayPropertySelectValue,
    filters=EbayPropertySelectValueFilter,
    order=EbayPropertySelectValueOrder,
    pagination=True,
    fields="__all__",
)
class EbayPropertySelectValueType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'EbaySalesChannelType',
        lazy("sales_channels.integrations.ebay.schema.types.types")
    ]
    ebay_property: EbayPropertyType
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
    EbaySalesChannelImport,
    filters=EbaySalesChannelImportFilter,
    order=EbaySalesChannelImportOrder,
    pagination=True,
    fields="__all__",
)
class EbaySalesChannelImportType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'EbaySalesChannelType',
        lazy("sales_channels.integrations.ebay.schema.types.types")
    ]

    @field()
    def import_id(self, info) -> str:
        return to_base64(ImportType, self.pk)

    @field()
    def proxy_id(self, info) -> str:
        from sales_channels.schema.types.types import SalesChannelImportType

        return to_base64(SalesChannelImportType, self.pk)


@type(
    EbaySalesChannelView,
    filters=EbaySalesChannelViewFilter,
    order=EbaySalesChannelViewOrder,
    pagination=True,
    fields="__all__",
)
class EbaySalesChannelViewType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'EbaySalesChannelType',
        lazy("sales_channels.integrations.ebay.schema.types.types")
    ]

    @field()
    def active(self, info) -> bool:
        return self.sales_channel.active


@type(
    EbayCurrency,
    filters=EbayCurrencyFilter,
    order=EbayCurrencyOrder,
    pagination=True,
    fields="__all__",
)
class EbayCurrencyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated[
        'EbaySalesChannelType',
        lazy("sales_channels.integrations.ebay.schema.types.types")
    ]
    sales_channel_view: Optional[Annotated[
        'EbaySalesChannelViewType',
        lazy("sales_channels.integrations.ebay.schema.types.types")
    ]]
    local_instance: Optional[Annotated[
        'CurrencyType',
        lazy("currencies.schema.types.types")
    ]]

    @field()
    def proxy_id(self, info) -> str:
        from sales_channels.schema.types.types import RemoteCurrencyType

        return to_base64(RemoteCurrencyType, self.pk)


@strawberry_type
class SuggestedEbayCategoryEntry:
    category_id: str
    category_name: str
    category_path: str
    leaf: bool


@strawberry_type
class SuggestedEbayCategory:
    category_tree_id: str
    categories: List[SuggestedEbayCategoryEntry]
