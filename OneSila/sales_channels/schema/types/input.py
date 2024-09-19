from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial, List

from sales_channels.models import ImportCurrency, ImportImage, ImportProcess, ImportProduct, ImportProperty, ImportPropertySelectValue, ImportVat, RemoteCategory, RemoteCurrency, RemoteCustomer, RemoteImage, RemoteImageProductAssociation, RemoteInventory, RemoteLog, RemoteOrder, RemotePrice, RemoteProduct, RemoteProductContent, RemoteProductProperty, RemoteProperty, RemotePropertySelectValue, RemoteTaskQueue, RemoteVat, SalesChannel, SalesChannelIntegrationPricelist, SalesChannelView, SalesChannelViewAssign


@input(ImportCurrency, fields="__all__")
class ImportCurrencyInput:
    pass


@partial(ImportCurrency, fields="__all__")
class ImportCurrencyPartialInput(NodeInput):
    pass

@input(ImportImage, fields="__all__")
class ImportImageInput:
    pass


@partial(ImportImage, fields="__all__")
class ImportImagePartialInput(NodeInput):
    pass

@input(ImportProcess, fields="__all__")
class ImportProcessInput:
    pass


@partial(ImportProcess, fields="__all__")
class ImportProcessPartialInput(NodeInput):
    pass

@input(ImportProduct, fields="__all__")
class ImportProductInput:
    pass


@partial(ImportProduct, fields="__all__")
class ImportProductPartialInput(NodeInput):
    pass

@input(ImportProperty, fields="__all__")
class ImportPropertyInput:
    pass


@partial(ImportProperty, fields="__all__")
class ImportPropertyPartialInput(NodeInput):
    pass

@input(ImportPropertySelectValue, fields="__all__")
class ImportPropertySelectValueInput:
    pass


@partial(ImportPropertySelectValue, fields="__all__")
class ImportPropertySelectValuePartialInput(NodeInput):
    pass

@input(ImportVat, fields="__all__")
class ImportVatInput:
    pass


@partial(ImportVat, fields="__all__")
class ImportVatPartialInput(NodeInput):
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

@input(RemotePrice, fields="__all__")
class RemotePriceInput:
    pass


@partial(RemotePrice, fields="__all__")
class RemotePricePartialInput(NodeInput):
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

@input(RemoteTaskQueue, fields="__all__")
class RemoteTaskQueueInput:
    pass


@partial(RemoteTaskQueue, fields="__all__")
class RemoteTaskQueuePartialInput(NodeInput):
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

@input(SalesChannelViewAssign, fields="__all__")
class SalesChannelViewAssignInput:
    pass


@partial(SalesChannelViewAssign, fields="__all__")
class SalesChannelViewAssignPartialInput(NodeInput):
    pass
