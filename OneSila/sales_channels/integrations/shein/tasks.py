from huey.contrib.djhuey import db_task
from sales_channels.integrations.shein.models.imports import SheinSalesChannelImport


@db_task()
def shein_import_db_task(import_process, sales_channel):
    """Dispatch the Shein schema import processor."""
    from sales_channels.integrations.shein.factories.imports.schema_imports import (
        SheinSchemaImportProcessor,
    )

    import_type = getattr(import_process, "type", SheinSalesChannelImport.TYPE_SCHEMA)
    if import_type == SheinSalesChannelImport.TYPE_SCHEMA:
        factory = SheinSchemaImportProcessor(
            import_process=import_process,
            sales_channel=sales_channel,
        )
        factory.run()


def run_shein_sales_channel_mapping_sync(
    *,
    source_sales_channel_id: int,
    target_sales_channel_id: int,
) -> dict:
    """Run the mapping sync factory for two Shein sales channels."""
    from sales_channels.integrations.shein.models import SheinSalesChannel
    from sales_channels.integrations.shein.factories.sync import (
        SheinSalesChannelMappingSyncFactory,
    )

    source = SheinSalesChannel.objects.get(id=source_sales_channel_id)
    target = SheinSalesChannel.objects.get(id=target_sales_channel_id)

    factory = SheinSalesChannelMappingSyncFactory(
        source_sales_channel=source,
        target_sales_channel=target,
    )
    return factory.run()


@db_task()
def shein_sync_sales_channel_mappings_task(
    source_sales_channel_id: int,
    target_sales_channel_id: int,
):
    """Huey task wrapper for SheinSalesChannelMappingSyncFactory."""
    return run_shein_sales_channel_mapping_sync(
        source_sales_channel_id=source_sales_channel_id,
        target_sales_channel_id=target_sales_channel_id,
    )


@db_task()
def shein_map_perfect_match_select_values_db_task(*, sales_channel_id: int):
    from sales_channels.integrations.shein.factories.auto_import import (
        SheinPerfectMatchSelectValueMappingFactory,
    )
    from sales_channels.integrations.shein.models import SheinSalesChannel

    sales_channel = SheinSalesChannel.objects.get(id=sales_channel_id)
    SheinPerfectMatchSelectValueMappingFactory(sales_channel=sales_channel).run()
