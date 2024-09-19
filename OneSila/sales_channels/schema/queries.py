from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type, field
from sales_channels.models import ImportCurrency, ImportImage, ImportProcess, ImportProduct, ImportProperty, ImportPropertySelectValue, ImportVat, RemoteCategory, RemoteCurrency, RemoteCustomer, RemoteImage, RemoteImageProductAssociation, RemoteInventory, RemoteLog, RemoteOrder, RemotePrice, RemoteProduct, RemoteProductContent, RemoteProductProperty, RemoteProperty, RemotePropertySelectValue, RemoteTaskQueue, RemoteVat, SalesChannel, SalesChannelIntegrationPricelist, SalesChannelView, SalesChannelViewAssign
from .types.types import ImportCurrencyType, ImportImageType, ImportProcessType, ImportProductType, ImportPropertyType, ImportPropertySelectValueType, ImportVatType, RemoteCategoryType, RemoteCurrencyType, RemoteCustomerType, RemoteImageType, RemoteImageProductAssociationType, RemoteInventoryType, RemoteLogType, RemoteOrderType, RemotePriceType, RemoteProductType, RemoteProductContentType, RemoteProductPropertyType, RemotePropertyType, RemotePropertySelectValueType, RemoteTaskQueueType, RemoteVatType, SalesChannelType, SalesChannelIntegrationPricelistType, SalesChannelViewType, SalesChannelViewAssignType


@type(name='Query')
class SalesChannelsQuery:
    import_process: ImportProcessType = node()
    import_processes: ListConnectionWithTotalCount[ImportProcessType] = connection()

    remote_log: RemoteLogType = node()
    remote_logs: ListConnectionWithTotalCount[RemoteLogType] = connection()

    remote_product: RemoteProductType = node()
    remote_products: ListConnectionWithTotalCount[RemoteProductType] = connection()

    remote_task_queue: RemoteTaskQueueType = node()
    remote_task_queues: ListConnectionWithTotalCount[RemoteTaskQueueType] = connection()

    sales_channel: SalesChannelType = node()
    sales_channels: ListConnectionWithTotalCount[SalesChannelType] = connection()

    sales_channel_integration_pricelist: SalesChannelIntegrationPricelistType = node()
    sales_channel_integration_pricelists: ListConnectionWithTotalCount[SalesChannelIntegrationPricelistType] = connection()

    sales_channel_view: SalesChannelViewType = node()
    sales_channel_views: ListConnectionWithTotalCount[SalesChannelViewType] = connection()

    sales_channel_view_assign: SalesChannelViewAssignType = node()
    sales_channel_view_assigns: ListConnectionWithTotalCount[SalesChannelViewAssignType] = connection()
