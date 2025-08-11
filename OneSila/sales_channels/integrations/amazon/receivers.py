from core.receivers import receiver
from core.signals import post_create, post_update
from sales_channels.signals import (
    refresh_website_pull_models,
    sales_channel_created,
    manual_sync_remote_product,
)
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonProductType,
)
from sales_channels.integrations.amazon.factories.sync.rule_sync import (
    AmazonPropertyRuleItemSyncFactory,
    AmazonProductTypeAsinSyncFactory,
)
from sales_channels.integrations.amazon.factories.sync.select_value_sync import (
    AmazonPropertySelectValuesSyncFactory,
)
from sales_channels.integrations.amazon.tasks import (
    create_amazon_product_type_rule_task,
    resync_amazon_product_db_task,
)
from imports_exports.signals import import_success
from sales_channels.integrations.amazon.factories.imports.products_imports import AmazonConfigurableVariationsFactory
from sales_channels.integrations.amazon.flows.tasks_runner import run_single_amazon_product_task_flow


@receiver(refresh_website_pull_models, sender='sales_channels.SalesChannel')
@receiver(sales_channel_created, sender='sales_channels.SalesChannel')
@receiver(refresh_website_pull_models, sender='amazon.AmazonSalesChannel')
@receiver(sales_channel_created, sender='amazon.AmazonSalesChannel')
def sales_channels__amazon__handle_pull_views(sender, instance, **kwargs):
    from sales_channels.integrations.amazon.factories.sales_channels.views import (
        AmazonSalesChannelViewPullFactory,
    )
    from sales_channels.integrations.amazon.factories.sales_channels.languages import (
        AmazonRemoteLanguagePullFactory,
    )
    from sales_channels.integrations.amazon.factories.sales_channels.currencies import (
        AmazonRemoteCurrencyPullFactory,
    )

    if not isinstance(instance.get_real_instance(), AmazonSalesChannel):
        return
    if not instance.refresh_token:
        return

    views_factory = AmazonSalesChannelViewPullFactory(sales_channel=instance)
    views_factory.run()

    languages_factory = AmazonRemoteLanguagePullFactory(sales_channel=instance)
    languages_factory.run()

    currencies_factory = AmazonRemoteCurrencyPullFactory(sales_channel=instance)
    currencies_factory.run()


@receiver(post_create, sender='amazon.AmazonProperty')
@receiver(post_update, sender='amazon.AmazonProperty')
def sales_channels__amazon_property__sync_rule_item(sender, instance: AmazonProperty, **kwargs):
    """Sync ProductPropertiesRuleItem when an Amazon property is mapped locally."""
    signal = kwargs.get('signal')
    if signal == post_update and not instance.is_dirty_field('local_instance', check_relationship=True):
        return
    if signal == post_create and not instance.local_instance:
        return

    sync_factory = AmazonPropertyRuleItemSyncFactory(instance)
    sync_factory.run()


@receiver(post_create, sender='amazon.AmazonProperty')
@receiver(post_update, sender='amazon.AmazonProperty')
def sales_channels__amazon_property__auto_map_select_values(sender, instance: AmazonProperty, **kwargs):
    """Automatically create local select values when duplicates exist across marketplaces."""
    signal = kwargs.get('signal')
    if signal == post_update and not instance.is_dirty_field('local_instance', check_relationship=True):
        return
    if signal == post_create and not instance.local_instance:
        return

    sync_factory = AmazonPropertySelectValuesSyncFactory(instance)
    sync_factory.run()


@receiver(post_update, sender='amazon.AmazonProperty')
def sales_channels__amazon_property__unmap_select_values(sender, instance: AmazonProperty, **kwargs):
    """Unmap select values when a property mapping changes."""
    if not instance.is_dirty_field('local_instance', check_relationship=True):
        return

    AmazonPropertySelectValue.objects.filter(
        amazon_property=instance,
        local_instance__isnull=False,
    ).update(local_instance=None)


@receiver(post_create, sender='amazon.AmazonProductType')
@receiver(post_update, sender='amazon.AmazonProductType')
def sales_channels__amazon_product_type__ensure_asin(sender, instance, **kwargs):
    signal = kwargs.get('signal')
    if signal == post_update and not instance.is_dirty_field('local_instance', check_relationship=True):
        return

    sync_factory = AmazonProductTypeAsinSyncFactory(instance)
    sync_factory.run()


@receiver(post_update, sender="amazon.AmazonProductType")
def sales_channels__amazon_product_type__imported_rule(sender, instance, **kwargs):
    if instance.is_dirty_field("imported") and instance.imported:
        create_amazon_product_type_rule_task(
            product_type_code=instance.product_type_code,
            sales_channel_id=instance.sales_channel_id,
        )


@receiver(import_success, sender='amazon.AmazonSalesChannelImport')
def sales_channels__amazon_import_completed(sender, instance, **kwargs):

    if instance.type != instance.TYPE_PRODUCTS:
        return

    factory = AmazonConfigurableVariationsFactory(import_process=instance)
    factory.run()


@receiver(manual_sync_remote_product, sender='amazon.AmazonProduct')
def amazon__product__manual_sync(sender, instance, view, force_validation_only=False, **kwargs):
    """Queue a task to resync an Amazon product."""
    product = instance.local_instance
    count = 1 + (getattr(product, 'get_configurable_variations', lambda: [])().count())

    run_single_amazon_product_task_flow(
        task_func=resync_amazon_product_db_task,
        view=view,
        number_of_remote_requests=count,
        product_id=product.id,
        remote_product_id=instance.id,
        force_validation_only=force_validation_only,
    )
