from huey.contrib.djhuey import db_task

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
