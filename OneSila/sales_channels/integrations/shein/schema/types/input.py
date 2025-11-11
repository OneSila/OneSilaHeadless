"""Input definitions for the Shein GraphQL schema."""

from core.schema.core.types.input import NodeInput, input, partial, strawberry_input
from sales_channels.integrations.shein.models import (
    SheinRemoteCurrency,
    SheinSalesChannel,
    SheinSalesChannelView,
)


@strawberry_input
class SheinValidateAuthInput:
    """Payload returned by Shein after a merchant authorizes the app."""
    app_id: str
    temp_token: str
    state: str


@input(SheinSalesChannel, exclude=["integration_ptr", "saleschannel_ptr"])
class SheinSalesChannelInput:
    """Create Shein sales channel input."""
    pass


@partial(SheinSalesChannel, fields="__all__")
class SheinSalesChannelPartialInput(NodeInput):
    """Partial input used for updates and lookups."""
    pass


@partial(SheinSalesChannelView, fields="__all__")
class SheinSalesChannelViewPartialInput(NodeInput):
    """Partial input for updating Shein storefront metadata."""
    pass


@partial(SheinRemoteCurrency, fields="__all__")
class SheinRemoteCurrencyPartialInput(NodeInput):
    """Partial input for updating Shein remote currencies."""
    pass
