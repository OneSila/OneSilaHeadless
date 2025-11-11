"""Strawberry types for the Shein integration."""

from typing import Annotated, Optional

from core.schema.core.types.types import (
    GetQuerysetMultiTenantMixin,
    field,
    lazy,
    relay,
    strawberry_type,
    type,
)
from strawberry.relay import to_base64

from sales_channels.integrations.shein.models import (
    SheinRemoteCurrency,
    SheinSalesChannel,
    SheinSalesChannelView,
)
from sales_channels.integrations.shein.schema.types.filters import (
    SheinRemoteCurrencyFilter,
    SheinSalesChannelFilter,
    SheinSalesChannelViewFilter,
)
from sales_channels.integrations.shein.schema.types.ordering import (
    SheinRemoteCurrencyOrder,
    SheinSalesChannelOrder,
    SheinSalesChannelViewOrder,
)


@strawberry_type
class SheinRedirectUrlType:
    """Container for the Shein authorization redirect link."""

    redirect_url: str


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
