from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial, List

from sales_channels.models import SalesChannelImport, RemoteCategory, RemoteCurrency, RemoteCustomer, RemoteImage, \
    RemoteImageProductAssociation, RemoteInventory, RemoteLog, RemoteOrder, RemotePrice, RemoteProduct, \
    RemoteProductContent, RemoteProductProperty, RemoteProperty, RemotePropertySelectValue, RemoteVat, SalesChannel, \
    SalesChannelIntegrationPricelist, SalesChannelView, SalesChannelViewAssign
from sales_channels.models.sales_channels import RemoteLanguage


@input(SalesChannelImport, fields="__all__")
class SalesChannelImportInput:
    pass


@partial(SalesChannelImport, fields="__all__")
class SalesChannelImportPartialInput(NodeInput):
    pass


@input(RemoteCategory, fields="__all__")
class RemoteCategoryInput:
    pass


@partial(RemoteCategory, fields="__all__")
class RemoteCategoryPartialInput(NodeInput):
    pass


@input(RemoteCurrency, fields="__all__")
class RemoteCurrencyInput:
    pass


@partial(RemoteCurrency, fields="__all__")
class RemoteCurrencyPartialInput(NodeInput):
    pass


@input(RemoteCustomer, fields="__all__")
class RemoteCustomerInput:
    pass


@partial(RemoteCustomer, fields="__all__")
class RemoteCustomerPartialInput(NodeInput):
    pass


@input(RemoteImage, fields="__all__")
class RemoteImageInput:
    pass


@partial(RemoteImage, fields="__all__")
class RemoteImagePartialInput(NodeInput):
    pass


@input(RemoteImageProductAssociation, fields="__all__")
class RemoteImageProductAssociationInput:
    pass


@partial(RemoteImageProductAssociation, fields="__all__")
class RemoteImageProductAssociationPartialInput(NodeInput):
    pass


@input(RemoteInventory, fields="__all__")
class RemoteInventoryInput:
    pass


@partial(RemoteInventory, fields="__all__")
class RemoteInventoryPartialInput(NodeInput):
    pass


@input(RemoteLog, fields="__all__")
class RemoteLogInput:
    pass


@partial(RemoteLog, fields="__all__")
class RemoteLogPartialInput(NodeInput):
    pass


@input(RemoteOrder, fields="__all__")
class RemoteOrderInput:
    pass


@partial(RemoteOrder, fields="__all__")
class RemoteOrderPartialInput(NodeInput):
    pass


@partial(RemoteOrder, fields="__all__")
class RemoteOrderPartialInput(NodeInput):
    pass


@input(RemotePrice, fields="__all__")
class RemotePriceInput:
    pass


@input(RemoteProduct, fields="__all__")
class RemoteProductInput:
    pass


@partial(RemoteProduct, fields="__all__")
class RemoteProductPartialInput(NodeInput):
    pass


@input(RemoteProductContent, fields="__all__")
class RemoteProductContentInput:
    pass


@partial(RemoteProductContent, fields="__all__")
class RemoteProductContentPartialInput(NodeInput):
    pass


@input(RemoteProductProperty, fields="__all__")
class RemoteProductPropertyInput:
    pass


@partial(RemoteProductProperty, fields="__all__")
class RemoteProductPropertyPartialInput(NodeInput):
    pass


@input(RemoteProperty, fields="__all__")
class RemotePropertyInput:
    pass


@partial(RemoteProperty, fields="__all__")
class RemotePropertyPartialInput(NodeInput):
    pass


@input(RemotePropertySelectValue, fields="__all__")
class RemotePropertySelectValueInput:
    pass


@partial(RemotePropertySelectValue, fields="__all__")
class RemotePropertySelectValuePartialInput(NodeInput):
    pass


@input(RemoteVat, fields="__all__")
class RemoteVatInput:
    pass


@partial(RemoteVat, fields="__all__")
class RemoteVatPartialInput(NodeInput):
    pass


@input(SalesChannel, fields="__all__")
class SalesChannelInput:
    pass


@partial(SalesChannel, fields="__all__")
class SalesChannelPartialInput(NodeInput):
    pass


@input(SalesChannelIntegrationPricelist, fields="__all__")
class SalesChannelIntegrationPricelistInput:
    pass


@partial(SalesChannelIntegrationPricelist, fields="__all__")
class SalesChannelIntegrationPricelistPartialInput(NodeInput):
    pass


@input(SalesChannelView, fields="__all__")
class SalesChannelViewInput:
    pass


@partial(SalesChannelView, fields="__all__")
class SalesChannelViewPartialInput(NodeInput):
    pass


@partial(RemoteLanguage, fields="__all__")
class RemoteLanguagePartialInput(NodeInput):
    pass


@input(SalesChannelViewAssign, fields="__all__")
class SalesChannelViewAssignInput:
    pass


@partial(SalesChannelViewAssign, fields="__all__")
class SalesChannelViewAssignPartialInput(NodeInput):
    pass
