from huey.contrib.djhuey import db_task

from core.huey import CRUCIAL_PRIORITY
from integrations.factories.remote_task import BaseRemoteTask
from sales_channels.decorators import remote_task
from sales_channels.integrations.shein.models.imports import SheinSalesChannelImport


@db_task()
def shein_import_db_task(import_process, sales_channel):
    """Dispatch the Shein import processor."""
    from sales_channels.integrations.shein.factories.imports.schema_imports import (
        SheinSchemaImportProcessor,
    )
    from sales_channels.integrations.shein.factories.imports.products import (
        SheinProductsAsyncImportProcessor,
    )

    import_type = getattr(import_process, "type", SheinSalesChannelImport.TYPE_SCHEMA)
    if import_type == SheinSalesChannelImport.TYPE_SCHEMA:
        factory = SheinSchemaImportProcessor(
            import_process=import_process,
            sales_channel=sales_channel,
        )
        factory.run()
    elif import_type == SheinSalesChannelImport.TYPE_PRODUCTS:
        factory = SheinProductsAsyncImportProcessor(
            import_process=import_process,
            sales_channel=sales_channel,
        )
        factory.run()


@db_task()
def shein_product_import_item_task(
    *,
    import_process_id: int,
    sales_channel_id: int,
    data: dict,
    is_last: bool = False,
    updated_with: int | None = None,
):
    from imports_exports.models import Import
    from sales_channels.integrations.shein.factories.imports.products import (
        SheinProductItemFactory,
    )
    from sales_channels.integrations.shein.models import SheinSalesChannel

    process = Import.objects.get(id=import_process_id)
    channel = SheinSalesChannel.objects.get(id=sales_channel_id)
    factory = SheinProductItemFactory(
        product_data=data.get("product", {}),
        offer_data=data.get("offer"),
        import_process=process,
        sales_channel=channel,
        is_last=is_last,
        updated_with=updated_with,
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


@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_shein_product_db_task(
    task_queue_item_id,
    *,
    sales_channel_id: int,
    product_id: int,
    view_id: int | None = None,
):
    """Run the Shein product creation factory."""
    # view_id is kept for backward compatibility with queued tasks.
    from products.models import Product
    from sales_channels.integrations.shein.factories.products.products import (
        SheinProductCreateFactory,
    )
    from sales_channels.integrations.shein.models import SheinSalesChannel

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task() -> None:
        factory = SheinProductCreateFactory(
            sales_channel=SheinSalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def resync_shein_product_db_task(
    task_queue_item_id,
    *,
    sales_channel_id: int,
    product_id: int,
    remote_product_id: int,
    view_id: int | None = None,
):
    """Run the Shein product resync factory."""
    # view_id is kept for backward compatibility with queued tasks.
    from products.models import Product
    from sales_channels.integrations.shein.factories.products.products import (
        SheinProductUpdateFactory,
    )
    from sales_channels.integrations.shein.models import SheinSalesChannel
    from sales_channels.models.products import RemoteProduct

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task() -> None:
        factory = SheinProductUpdateFactory(
            sales_channel=SheinSalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
            remote_instance=RemoteProduct.objects.get(id=remote_product_id),
        )
        factory.run()

    task.execute(actual_task)
