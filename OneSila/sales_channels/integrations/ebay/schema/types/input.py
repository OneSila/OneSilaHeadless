from core.schema.core.types.input import NodeInput, input, partial, strawberry_input
from sales_channels.integrations.ebay.models import (
    EbaySalesChannel,
    EbayInternalProperty,
    EbayProductType,
    EbayProperty,
    EbayPropertySelectValue,
    EbaySalesChannelImport,
    EbaySalesChannelView,
    EbayCurrency,
)


@strawberry_input
class EbayValidateAuthInput:
    code: str
    state: str


@input(EbaySalesChannel, exclude=['integration_ptr', 'saleschannel_ptr'])
class EbaySalesChannelInput:
    pass


@partial(EbaySalesChannel, fields="__all__")
class EbaySalesChannelPartialInput(NodeInput):
    pass


@input(EbayProperty, fields="__all__")
class EbayPropertyInput:
    pass


@partial(EbayProperty, fields="__all__")
class EbayPropertyPartialInput(NodeInput):
    pass


@input(EbayInternalProperty, fields="__all__")
class EbayInternalPropertyInput:
    pass


@partial(EbayInternalProperty, fields="__all__")
class EbayInternalPropertyPartialInput(NodeInput):
    pass


@partial(EbayProductType, fields="__all__")
class EbayProductTypePartialInput(NodeInput):
    pass


@input(EbayPropertySelectValue, fields="__all__")
class EbayPropertySelectValueInput:
    pass


@partial(EbayPropertySelectValue, fields="__all__")
class EbayPropertySelectValuePartialInput(NodeInput):
    pass


@input(EbaySalesChannelImport, exclude=['saleschannelimport_ptr', 'import_ptr'])
class EbaySalesChannelImportInput:
    pass


@partial(EbaySalesChannelImport, fields="__all__")
class EbaySalesChannelImportPartialInput(NodeInput):
    pass


@input(EbaySalesChannelView, fields="__all__")
class EbaySalesChannelViewInput:
    pass


@partial(EbaySalesChannelView, fields="__all__")
class EbaySalesChannelViewPartialInput(NodeInput):
    pass


@partial(EbayCurrency, fields="__all__")
class EbayCurrencyPartialInput(NodeInput):
    pass
