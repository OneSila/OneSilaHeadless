from core.schema.core.mutations import create, update, delete, type, List, field
from .fields import resync_sales_channel_assign
from ..types.types import SalesChannelType, SalesChannelIntegrationPricelistType, SalesChannelViewType, \
    SalesChannelViewAssignType, ImportProcessType
from ..types.input import ImportProcessInput, ImportProcessPartialInput, SalesChannelInput, SalesChannelPartialInput, SalesChannelIntegrationPricelistInput, SalesChannelIntegrationPricelistPartialInput, SalesChannelViewInput, SalesChannelViewPartialInput, SalesChannelViewAssignInput, SalesChannelViewAssignPartialInput


@type(name='Mutation')
class SalesChannelsMutation:
    create_import_process: ImportProcessType = create(ImportProcessInput)
    create_import_processes: List[ImportProcessType] = create(ImportProcessInput)
    update_import_process: ImportProcessType = update(ImportProcessPartialInput)
    delete_import_process: ImportProcessType = delete()
    delete_import_processes: List[ImportProcessType] = delete()

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

    create_sales_channel_view_assign: SalesChannelViewAssignType = create(SalesChannelViewAssignInput)
    resync_sales_channel_view_assign: SalesChannelViewAssignType = resync_sales_channel_assign()
    create_sales_channel_view_assigns: List[SalesChannelViewAssignType] = create(SalesChannelViewAssignInput)
    update_sales_channel_view_assign: SalesChannelViewAssignType = update(SalesChannelViewAssignPartialInput)
    delete_sales_channel_view_assign: SalesChannelViewAssignType = delete()
    delete_sales_channel_view_assigns: List[SalesChannelViewAssignType] = delete()
