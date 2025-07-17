from huey.contrib.djhuey import db_task
from core.huey import LOW_PRIORITY
from sales_channels.decorators import remote_task


@remote_task(priority=LOW_PRIORITY)
@db_task()
def amazon_import_db_task(import_process, sales_channel):
    from sales_channels.integrations.amazon.factories.imports.schema_imports import AmazonSchemaImportProcessor
    from sales_channels.integrations.amazon.factories.imports.products_imports import AmazonProductsImportProcessor
    from sales_channels.integrations.amazon.models import AmazonSalesChannelImport

    if import_process.type == AmazonSalesChannelImport.TYPE_SCHEMA:
        fac = AmazonSchemaImportProcessor(import_process=import_process, sales_channel=sales_channel)
        fac.run()
    elif import_process.type == AmazonSalesChannelImport.TYPE_PRODUCTS:
        fac = AmazonProductsImportProcessor(import_process=import_process, sales_channel=sales_channel)
        fac.run()
