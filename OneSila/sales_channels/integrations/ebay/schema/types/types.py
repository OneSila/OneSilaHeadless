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
    EbayProperty,
    EbaySalesChannelView,
)
from sales_channels.integrations.ebay.schema.types.filters import (
    EbaySalesChannelFilter,
    EbayPropertyFilter,
    EbaySalesChannelViewFilter,
)
from sales_channels.integrations.ebay.schema.types.ordering import (
    EbaySalesChannelOrder,
    EbayPropertyOrder,
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
    # select_values: List[Annotated[
    #     'EbayPropertySelectValueType',
    #     lazy("sales_channels.integrations.ebay.schema.types.types")
    # ]]


# @type(
#     EbayPropertySelectValue,
#     filters=EbayPropertySelectValueFilter,
#     order=EbayPropertySelectValueOrder,
#     pagination=True,
#     fields="__all__",
# )
# class EbayPropertySelectValueType(relay.Node, GetQuerysetMultiTenantMixin):
#     sales_channel: Annotated[
#         'EbaySalesChannelType',
#         lazy("sales_channels.integrations.ebay.schema.types.types")
#     ]
#     ebay_property: EbayPropertyType
#     marketplace: Annotated[
#         'SalesChannelViewType',
#         lazy("sales_channels.schema.types.types")
#     ]
#     local_instance: Optional[Annotated[
#         'PropertySelectValueType',
#         lazy("properties.schema.types.types")
#     ]]


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
