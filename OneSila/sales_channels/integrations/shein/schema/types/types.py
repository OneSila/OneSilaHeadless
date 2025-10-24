"""Strawberry types for the Shein integration."""

from core.schema.core.types.types import (
    GetQuerysetMultiTenantMixin,
    field,
    relay,
    strawberry_type,
    type,
)
from sales_channels.integrations.shein.models import SheinSalesChannel


@strawberry_type
class SheinRedirectUrlType:
    """Container for the Shein authorization redirect link."""

    redirect_url: str


@type(SheinSalesChannel, pagination=True, fields="__all__")
class SheinSalesChannelType(relay.Node, GetQuerysetMultiTenantMixin):
    """Expose Shein sales channel fields through GraphQL."""

    @field()
    def integration_ptr(self, info) -> str:
        return self.integration_ptr

    @field()
    def saleschannel_ptr(self, info) -> str:
        return self.saleschannel_ptr
