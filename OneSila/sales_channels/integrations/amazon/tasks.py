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


@db_task(priority=HIGH_PRIORITY)
def amazon_refresh_product_import_task(product_id: int, view_id: int):
    from products.models import Product
    from sales_channels.integrations.amazon.factories.imports.product_import import AmazonProductImportFactory
    from sales_channels.integrations.amazon.models import AmazonSalesChannelView

    product = Product.objects.get(id=product_id)
    view = AmazonSalesChannelView.objects.select_related("sales_channel").get(id=view_id)

    factory = AmazonProductImportFactory(product=product, view=view)
    factory.run()


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


@db_task()
def amazon_auto_import_select_value_task(select_value_id: int):
    from sales_channels.integrations.amazon.models import AmazonPropertySelectValue
    from sales_channels.integrations.amazon.factories.auto_import import (
        AmazonAutoImportSelectValueFactory,
    )

    select_value = AmazonPropertySelectValue.objects.get(id=select_value_id)
    fac = AmazonAutoImportSelectValueFactory(select_value)
    fac.run()


@db_task()
def amazon_translate_select_value_task(select_value_id: int):
    from sales_channels.integrations.amazon.models import AmazonPropertySelectValue
    from sales_channels.integrations.amazon.constants import (
        AMAZON_SELECT_VALUE_TRANSLATION_IGNORE_CODES,
    )
    from llm.factories.remote_taxonomy_translator import RemoteSelectValueTranslationLLM

    instance = AmazonPropertySelectValue.objects.get(id=select_value_id)

    remote_language_obj = instance.marketplace.remote_languages.first()
    remote_lang = remote_language_obj.local_instance if remote_language_obj else None
    company_lang = instance.sales_channel.multi_tenant_company.language

    remote_name = instance.remote_name or instance.remote_value

    if instance.amazon_property.code in AMAZON_SELECT_VALUE_TRANSLATION_IGNORE_CODES:
        translated = remote_name
    elif not remote_lang or remote_lang == company_lang:
        translated = remote_name
    else:
        translator = RemoteSelectValueTranslationLLM(
            integration_label="Amazon",
            remote_name=remote_name,
            from_language_code=remote_lang,
            to_language_code=company_lang,
            property_name=instance.amazon_property.name,
            property_code=instance.amazon_property.code,
        )
        try:
            translated = translator.translate()
        except Exception:
            translated = remote_name

    instance.translated_remote_name = translated
    instance.save(update_fields=["translated_remote_name"])


def run_amazon_sales_channel_mapping_sync(
    *,
    source_sales_channel_id: int,
    target_sales_channel_id: int,
) -> dict:
    """Run the mapping sync factory for two Amazon sales channels."""
    from sales_channels.integrations.amazon.models import AmazonSalesChannel
    from sales_channels.integrations.amazon.factories.sync import (
        AmazonSalesChannelMappingSyncFactory,
    )

    source = AmazonSalesChannel.objects.get(id=source_sales_channel_id)
    target = AmazonSalesChannel.objects.get(id=target_sales_channel_id)

    factory = AmazonSalesChannelMappingSyncFactory(
        source_sales_channel=source,
        target_sales_channel=target,
    )
    return factory.run()


@db_task()
def amazon_sync_sales_channel_mappings_task(
    source_sales_channel_id: int,
    target_sales_channel_id: int,
):
    """Huey task wrapper for AmazonSalesChannelMappingSyncFactory."""
    return run_amazon_sales_channel_mapping_sync(
        source_sales_channel_id=source_sales_channel_id,
        target_sales_channel_id=target_sales_channel_id,
    )


@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_amazon_product_db_task(
    task_queue_item_id,
    sales_channel_id,
    product_id,
    view_id,
    force_validation_only=False,
):
    """Run the create factory for an Amazon product."""
    from products.models import Product
    from .models import AmazonSalesChannel, AmazonSalesChannelView
    from .factories.products import AmazonProductCreateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        factory = AmazonProductCreateFactory(
            sales_channel=AmazonSalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
            view=AmazonSalesChannelView.objects.get(id=view_id),
            force_validation_only=force_validation_only,
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def resync_amazon_product_db_task(
    task_queue_item_id,
    sales_channel_id,
    product_id,
    remote_product_id,
    view_id,
    force_validation_only=False,
    force_full_update=False,
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
            force_full_update=force_full_update,
        )
        factory.run()

    task.execute(actual_task)


@db_periodic_task(crontab(minute='*/15'))
def refresh_amazon_product_issues_cronjob():
    """Fetch latest listing issues for Amazon products synced in the last 15 minutes."""
    from datetime import timedelta
    from django.utils import timezone
    from .models import AmazonProduct, AmazonSalesChannelView
    from .factories.sales_channels.issues import FetchRemoteIssuesFactory

    cutoff = timezone.now() - timedelta(minutes=15)
    products = AmazonProduct.objects.filter(last_sync_at__gte=cutoff)
    for product in products.iterator():
        marketplaces = product.created_marketplaces or []
        views = AmazonSalesChannelView.objects.filter(
            sales_channel=product.sales_channel, remote_id__in=marketplaces
        )
        for view in views:
            fac = FetchRemoteIssuesFactory(remote_product=product, view=view)
            fac.run()


@db_periodic_task(crontab(minute='0', hour='0', day='1'))
def refresh_amazon_browse_nodes_cronjob():
    """Refresh Amazon browse nodes for all marketplaces once a month."""
    from .factories.recommended_browse_nodes import AmazonBrowseNodeRefreshFactory

    fac = AmazonBrowseNodeRefreshFactory()
    fac.run()
