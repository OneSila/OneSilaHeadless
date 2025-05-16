from core.schema.core.queries import node, connection, DjangoListConnection, type, field
from .types.types import RemoteLogType, RemoteProductType, SalesChannelType, \
    SalesChannelIntegrationPricelistType, SalesChannelViewType, SalesChannelViewAssignType, RemoteLanguageType, \
    RemoteCurrencyType, SalesChannelImportType, IntegrationType


@type(name='Query')
class SalesChannelsQuery:
    sales_channel_import: SalesChannelImportType = node()
    sales_channel_imports: DjangoListConnection[SalesChannelImportType] = connection()

    remote_log: RemoteLogType = node()
    remote_logs: DjangoListConnection[RemoteLogType] = connection()

    remote_product: RemoteProductType = node()
    remote_products: DjangoListConnection[RemoteProductType] = connection()

    sales_channel: SalesChannelType = node()
    sales_channels: DjangoListConnection[SalesChannelType] = connection()

    sales_channel_integration_pricelist: SalesChannelIntegrationPricelistType = node()
    sales_channel_integration_pricelists: DjangoListConnection[SalesChannelIntegrationPricelistType] = connection()

    sales_channel_view: SalesChannelViewType = node()
    sales_channel_views: DjangoListConnection[SalesChannelViewType] = connection()

    remote_language: RemoteLanguageType = node()
    remote_languages: DjangoListConnection[RemoteLanguageType] = connection()

    remote_currency: RemoteCurrencyType = node()
    remote_currencies: DjangoListConnection[RemoteCurrencyType] = connection()

    sales_channel_view_assign: SalesChannelViewAssignType = node()
    sales_channel_view_assigns: DjangoListConnection[SalesChannelViewAssignType] = connection()

    integration: IntegrationType = node()
