from typing import Annotated, Optional, List

from core.schema.core.types.types import (
    relay,
    type,
    GetQuerysetMultiTenantMixin,
    strawberry_type,
    field,
    lazy,
)
from sales_channels.integrations.ebay.models import (
    EbaySalesChannel,
    EbayInternalProperty,
    EbayProductType,
    EbayProductTypeItem,
    EbayProperty,
    EbayPropertySelectValue,
    EbaySalesChannelView,
)
from sales_channels.integrations.ebay.schema.types.filters import (
    EbaySalesChannelFilter,
    EbayInternalPropertyFilter,
    EbayProductTypeFilter,
    EbayProductTypeItemFilter,
    EbayPropertyFilter,
    EbayPropertySelectValueFilter,
    EbaySalesChannelViewFilter,
)
from sales_channels.integrations.ebay.schema.types.ordering import (
    EbaySalesChannelOrder,
    EbayInternalPropertyOrder,
    EbayProductTypeOrder,
    EbayProductTypeItemOrder,
    EbayPropertyOrder,
    EbayPropertySelectValueOrder,
    EbaySalesChannelViewOrder,
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
