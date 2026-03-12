from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task

from sales_channels.integrations.mirakl.factories.imports.schema_imports import (
    MiraklSchemaImportProcessor,
)
from sales_channels.integrations.mirakl.models import MiraklSalesChannelImport


@db_task()
def mirakl_import_db_task(*, import_process, sales_channel):
    """Dispatch the Mirakl import processor."""
    import_type = getattr(import_process, "type", MiraklSalesChannelImport.TYPE_SCHEMA)
    if import_type == MiraklSalesChannelImport.TYPE_SCHEMA:
        factory = MiraklSchemaImportProcessor(
            import_process=import_process,
            sales_channel=sales_channel,
        )
        factory.run()


@db_periodic_task(crontab(minute="*/20"))
def sales_channels__tasks__sync_mirakl_product_feeds__cronjob():
    from sales_channels.integrations.mirakl.flows import process_mirakl_gathering_product_feeds

    process_mirakl_gathering_product_feeds()


@db_periodic_task(crontab(minute="*/5"))
def sales_channels__tasks__refresh_mirakl_imports__cronjob():
    from sales_channels.integrations.mirakl.flows import refresh_mirakl_imports

    refresh_mirakl_imports()


@db_task()
def sales_channels__tasks__sync_mirakl_product_feeds(*, sales_channel_id: int | None = None, force: bool = False):
    from sales_channels.integrations.mirakl.flows import process_mirakl_gathering_product_feeds

    return process_mirakl_gathering_product_feeds(sales_channel_id=sales_channel_id, force=force)


@db_task()
def sales_channels__tasks__refresh_mirakl_imports(*, import_process_id: int | None = None, sales_channel_id: int | None = None):
    from sales_channels.integrations.mirakl.flows import refresh_mirakl_imports

    return refresh_mirakl_imports(
        import_process_id=import_process_id,
        sales_channel_id=sales_channel_id,
    )


@db_task()
def sales_channels__tasks__retry_mirakl_feed(*, feed_id: int):
    from sales_channels.integrations.mirakl.flows import retry_mirakl_feed

    return retry_mirakl_feed(feed_id=feed_id)
