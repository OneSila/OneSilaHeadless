from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from sales_channels.models import ImportCurrency, ImportImage, ImportProcess, ImportProduct, ImportProperty, ImportPropertySelectValue, ImportVat, RemoteCategory, RemoteCurrency, RemoteCustomer, RemoteImage, RemoteImageProductAssociation, RemoteInventory, RemoteLog, RemoteOrder, RemotePrice, RemoteProduct, RemoteProductContent, RemoteProductProperty, RemoteProperty, RemotePropertySelectValue, RemoteTaskQueue, RemoteVat, SalesChannel, SalesChannelIntegrationPricelist, SalesChannelView, SalesChannelViewAssign


@order(ImportCurrency)
class ImportCurrencyOrder:
    id: auto


@order(ImportImage)
class ImportImageOrder:
    id: auto


@order(ImportProcess)
class ImportProcessOrder:
    id: auto


@order(ImportProduct)
class ImportProductOrder:
    id: auto


@order(ImportProperty)
class ImportPropertyOrder:
    id: auto


@order(ImportPropertySelectValue)
class ImportPropertySelectValueOrder:
    id: auto


@order(ImportVat)
class ImportVatOrder:
    id: auto


@order(RemoteCategory)
class RemoteCategoryOrder:
    id: auto


@order(RemoteCurrency)
class RemoteCurrencyOrder:
    id: auto


@order(RemoteCustomer)
class RemoteCustomerOrder:
    id: auto


@order(RemoteImage)
class RemoteImageOrder:
    id: auto


@order(RemoteImageProductAssociation)
class RemoteImageProductAssociationOrder:
    id: auto


@order(RemoteInventory)
class RemoteInventoryOrder:
    id: auto


@order(RemoteLog)
class RemoteLogOrder:
    id: auto


@order(RemoteOrder)
class RemoteOrderOrder:
    id: auto


@order(RemotePrice)
class RemotePriceOrder:
    id: auto


@order(RemoteProduct)
class RemoteProductOrder:
    id: auto


@order(RemoteProductContent)
class RemoteProductContentOrder:
    id: auto


@order(RemoteProductProperty)
class RemoteProductPropertyOrder:
    id: auto


@order(RemoteProperty)
class RemotePropertyOrder:
    id: auto


@order(RemotePropertySelectValue)
class RemotePropertySelectValueOrder:
    id: auto


@order(RemoteTaskQueue)
class RemoteTaskQueueOrder:
    id: auto


@order(RemoteVat)
class RemoteVatOrder:
    id: auto


@order(SalesChannel)
class SalesChannelOrder:
    id: auto


@order(SalesChannelIntegrationPricelist)
class SalesChannelIntegrationPricelistOrder:
    id: auto


@order(SalesChannelView)
class SalesChannelViewOrder:
    id: auto


@order(SalesChannelViewAssign)
class SalesChannelViewAssignOrder:
    id: auto

