from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type, field
from integrations.schema.types.types import IntegrationType
from .types.types import RemoteLogType, RemoteProductType, SalesChannelType, \
    SalesChannelIntegrationPricelistType, SalesChannelViewType, SalesChannelViewAssignType, RemoteLanguageType, \
    RemoteCurrencyType, SalesChannelImportType

@type(name='Query')
class SalesChannelsQuery:
    sales_channel_import: SalesChannelImportType = node()
    sales_channel_imports: ListConnectionWithTotalCount[SalesChannelImportType] = connection()

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

    remote_language: RemoteLanguageType = node()
    remote_languages: ListConnectionWithTotalCount[RemoteLanguageType] = connection()

    remote_currency: RemoteCurrencyType = node()
    remote_currencies: ListConnectionWithTotalCount[RemoteCurrencyType] = connection()

    sales_channel_view_assign: SalesChannelViewAssignType = node()
    sales_channel_view_assigns: ListConnectionWithTotalCount[SalesChannelViewAssignType] = connection()

    integration: IntegrationType = node()
