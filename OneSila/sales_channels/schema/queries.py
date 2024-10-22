from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type, field
from .types.types import ImportProcessType, RemoteLogType, RemoteProductType, SalesChannelType, SalesChannelIntegrationPricelistType, SalesChannelViewType, SalesChannelViewAssignType


@type(name='Query')
class SalesChannelsQuery:
    import_process: ImportProcessType = node()
    import_processes: ListConnectionWithTotalCount[ImportProcessType] = connection()

    remote_log: RemoteLogType = node()
    remote_logs: ListConnectionWithTotalCount[RemoteLogType] = connection()

    remote_product: RemoteProductType = node()
    remote_products: ListConnectionWithTotalCount[RemoteProductType] = connection()

    sales_channel: SalesChannelType = node()
    sales_channels: ListConnectionWithTotalCount[SalesChannelType] = connection()

    sales_channel_integration_pricelist: SalesChannelIntegrationPricelistType = node()
    sales_channel_integration_pricelists: ListConnectionWithTotalCount[SalesChannelIntegrationPricelistType] = connection()

    sales_channel_view: SalesChannelViewType = node()
    sales_channel_views: ListConnectionWithTotalCount[SalesChannelViewType] = connection()

    sales_channel_view_assign: SalesChannelViewAssignType = node()
    sales_channel_view_assigns: ListConnectionWithTotalCount[SalesChannelViewAssignType] = connection()
