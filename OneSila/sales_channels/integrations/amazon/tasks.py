from huey.contrib.djhuey import db_task
from core.huey import LOW_PRIORITY
from sales_channels.decorators import remote_task
from core.decorators import run_task_after_commit


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


@run_task_after_commit
@db_task()
def create_amazon_product_type_rule_task(product_type_code: str, sales_channel_id: int):
    """Create local properties rule for an imported product type."""
    from sales_channels.integrations.amazon.factories.sales_channels.full_schema import (
        AmazonProductTypeRuleFactory,
    )
    from sales_channels.integrations.amazon.models import AmazonSalesChannel

    sales_channel = AmazonSalesChannel.objects.get(id=sales_channel_id)
    fac = AmazonProductTypeRuleFactory(
        product_type_code=product_type_code,
        sales_channel=sales_channel,
    )
    fac.run()
