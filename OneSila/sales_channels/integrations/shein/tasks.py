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
