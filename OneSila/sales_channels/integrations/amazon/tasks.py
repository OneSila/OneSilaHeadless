from huey import crontab
from huey.contrib.djhuey import db_task, db_periodic_task
from core.huey import LOW_PRIORITY, HIGH_PRIORITY, CRUCIAL_PRIORITY
from sales_channels.decorators import remote_task
from core.decorators import run_task_after_commit
from integrations.factories.remote_task import BaseRemoteTask


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


@db_task(priority=HIGH_PRIORITY)
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


# @run_task_after_commit
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


@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def resync_amazon_product_db_task(
    task_queue_item_id,
    sales_channel_id,
    product_id,
    remote_product_id,
    view_id,
    force_validation_only=False,
):
    """Run the resync factory for an Amazon product."""
    from products.models import Product
    from .models import AmazonSalesChannel, AmazonProduct, AmazonSalesChannelView
    from .factories.products import AmazonProductSyncFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        factory = AmazonProductSyncFactory(
            sales_channel=AmazonSalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
            remote_instance=AmazonProduct.objects.get(id=remote_product_id),
            view=AmazonSalesChannelView.objects.get(id=view_id),
            force_validation_only=force_validation_only,
        )
        factory.run()

    task.execute(actual_task)


@db_periodic_task(crontab(minute='0', hour='0,12'))
def refresh_amazon_product_issues_cronjob():
    """Fetch latest listing issues for Amazon products synced in the last 12 hours."""
    from datetime import timedelta
    from django.utils import timezone
    from .models import AmazonProduct, AmazonSalesChannelView
    from .factories.sales_channels.issues import FetchRemoteIssuesFactory

    cutoff = timezone.now() - timedelta(hours=12)
    products = AmazonProduct.objects.filter(last_sync_at__gte=cutoff)
    for product in products.iterator():
        marketplaces = product.created_marketplaces or []
        views = AmazonSalesChannelView.objects.filter(
            sales_channel=product.sales_channel, remote_id__in=marketplaces
        )
        for view in views:
            fac = FetchRemoteIssuesFactory(remote_product=product, view=view)
            fac.run()
