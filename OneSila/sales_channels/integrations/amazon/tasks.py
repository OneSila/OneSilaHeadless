from huey.contrib.djhuey import db_task
from core.huey import LOW_PRIORITY, HIGH_PRIORITY
from sales_channels.decorators import remote_task
from core.decorators import run_task_after_commit


@db_task()
def amazon_import_db_task(import_process, sales_channel):
    from sales_channels.integrations.amazon.factories.imports.schema_imports import AmazonSchemaImportProcessor
    from sales_channels.integrations.amazon.factories.imports.products_imports import AmazonProductsImportProcessor
    from sales_channels.integrations.amazon.models import AmazonSalesChannelImport
    from sales_channels.integrations.amazon.factories.imports.products_imports import AmazonProductsAsyncImportProcessor

    if import_process.type == AmazonSalesChannelImport.TYPE_SCHEMA:
        fac = AmazonSchemaImportProcessor(import_process=import_process, sales_channel=sales_channel)
        fac.run()
    elif import_process.type == AmazonSalesChannelImport.TYPE_PRODUCTS:

        fac = AmazonProductsAsyncImportProcessor(import_process=import_process, sales_channel=sales_channel)
        fac.run()


@db_task()
def amazon_product_import_item_task(
    import_process_id, sales_channel_id, product_data, is_last=False, updated_with=None
):
    from sales_channels.integrations.amazon.factories.imports.products_imports import AmazonProductItemFactory
    from imports_exports.models import Import
    from sales_channels.integrations.amazon.models import AmazonSalesChannel

    process = Import.objects.get(id=import_process_id)
    channel = AmazonSalesChannel.objects.get(id=sales_channel_id)
    fac = AmazonProductItemFactory(
        product_data=product_data,
        import_process=process,
        sales_channel=channel,
        is_last=is_last,
        updated_with=updated_with,
    )
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
