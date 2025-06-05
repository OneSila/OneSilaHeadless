from core.schema.core.types.input import NodeInput, input, partial, strawberry_input
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProperty,
    AmazonPropertySelectValue,
)


@input(AmazonSalesChannel, exclude=['integration_ptr', 'saleschannel_ptr'])
class AmazonSalesChannelInput:
    pass


@partial(AmazonSalesChannel, fields="__all__")
class AmazonSalesChannelPartialInput(NodeInput):
    pass


@input(AmazonProperty, fields="__all__")
class AmazonPropertyInput:
    pass


@partial(AmazonProperty, fields="__all__")
class AmazonPropertyPartialInput(NodeInput):
    pass


@input(AmazonPropertySelectValue, fields="__all__")
class AmazonPropertySelectValueInput:
    pass


@partial(AmazonPropertySelectValue, fields="__all__")
class AmazonPropertySelectValuePartialInput(NodeInput):
    pass


@strawberry_input
class AmazonValidateAuthInput:
    spapi_oauth_code: str
    selling_partner_id: str
    state: str
