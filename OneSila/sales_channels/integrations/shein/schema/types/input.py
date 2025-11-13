"""Input definitions for the Shein GraphQL schema."""

from core.schema.core.types.input import NodeInput, input, partial, strawberry_input
from sales_channels.integrations.shein.models import (
    SheinInternalProperty,
    SheinInternalPropertyOption,
    SheinProperty,
    SheinPropertySelectValue,
    SheinProductType,
    SheinRemoteCurrency,
    SheinSalesChannel,
    SheinSalesChannelView,
    SheinSalesChannelImport,
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


@partial(SheinProperty, fields="__all__")
class SheinPropertyPartialInput(NodeInput):
    """Partial input for updating Shein remote properties."""
    pass


@partial(SheinPropertySelectValue, fields="__all__")
class SheinPropertySelectValuePartialInput(NodeInput):
    """Partial input for updating Shein property select values."""
    pass


@partial(SheinProductType, fields="__all__")
class SheinProductTypePartialInput(NodeInput):
    """Partial input for updating Shein product types."""
    pass


@partial(SheinInternalProperty, fields="__all__")
class SheinInternalPropertyPartialInput(NodeInput):
    """Partial input for updating Shein internal properties."""
    pass


@partial(SheinInternalPropertyOption, fields="__all__")
class SheinInternalPropertyOptionPartialInput(NodeInput):
    """Partial input for updating Shein internal property options."""
    pass


@input(
    SheinSalesChannelImport,
    exclude=["saleschannelimport_ptr", "import_ptr"],
)
class SheinSalesChannelImportInput:
    """Create Shein import process input."""
    pass


@partial(SheinSalesChannelImport, fields="__all__")
class SheinSalesChannelImportPartialInput(NodeInput):
    """Partial input for updating Shein import processes."""
    pass
