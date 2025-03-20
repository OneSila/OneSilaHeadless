from core.schema.core.mutations import create, update, delete, type, List, field
from .fields import resync_sales_channel_assign
from ..types.types import SalesChannelType, SalesChannelIntegrationPricelistType, SalesChannelViewType, \
    SalesChannelViewAssignType, SalesChannelImportType, RemoteLanguageType, RemoteCurrencyType
from ..types.input import SalesChannelImportInput, SalesChannelImportPartialInput, SalesChannelInput, SalesChannelPartialInput, \
    SalesChannelIntegrationPricelistInput, SalesChannelIntegrationPricelistPartialInput, SalesChannelViewInput, \
    SalesChannelViewPartialInput, SalesChannelViewAssignInput, SalesChannelViewAssignPartialInput, \
    RemoteLanguagePartialInput, RemoteCurrencyPartialInput


@type(name='Mutation')
class SalesChannelsMutation:
    create_import_process: SalesChannelImportType = create(SalesChannelImportInput)
    create_import_processes: List[SalesChannelImportType] = create(SalesChannelImportInput)
    update_import_process: SalesChannelImportType = update(SalesChannelImportPartialInput)
    delete_import_process: SalesChannelImportType = delete()
    delete_import_processes: List[SalesChannelImportType] = delete()

    create_sales_channel: SalesChannelType = create(SalesChannelInput)
    create_sales_channels: List[SalesChannelType] = create(SalesChannelInput)
    update_sales_channel: SalesChannelType = update(SalesChannelPartialInput)
    delete_sales_channel: SalesChannelType = delete()
    delete_sales_channels: List[SalesChannelType] = delete()

    create_sales_channel_integration_pricelist: SalesChannelIntegrationPricelistType = create(SalesChannelIntegrationPricelistInput)
    create_sales_channel_integration_pricelists: List[SalesChannelIntegrationPricelistType] = create(SalesChannelIntegrationPricelistInput)
    update_sales_channel_integration_pricelist: SalesChannelIntegrationPricelistType = update(SalesChannelIntegrationPricelistPartialInput)
    delete_sales_channel_integration_pricelist: SalesChannelIntegrationPricelistType = delete()
    delete_sales_channel_integration_pricelists: List[SalesChannelIntegrationPricelistType] = delete()

    update_sales_channel_view: SalesChannelViewType = update(SalesChannelViewPartialInput)
    update_remote_language: RemoteLanguageType = update(RemoteLanguagePartialInput)
    update_remote_currency: RemoteCurrencyType = update(RemoteCurrencyPartialInput)

    create_sales_channel_view_assign: SalesChannelViewAssignType = create(SalesChannelViewAssignInput)
    resync_sales_channel_view_assign: SalesChannelViewAssignType = resync_sales_channel_assign()
    create_sales_channel_view_assigns: List[SalesChannelViewAssignType] = create(SalesChannelViewAssignInput)
    update_sales_channel_view_assign: SalesChannelViewAssignType = update(SalesChannelViewAssignPartialInput)
    delete_sales_channel_view_assign: SalesChannelViewAssignType = delete()
    delete_sales_channel_view_assigns: List[SalesChannelViewAssignType] = delete()
