from core.receivers import receiver
from core.signals import post_create, post_update
from sales_channels.signals import refresh_website_pull_models, sales_channel_created
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProperty,
)
from sales_channels.integrations.amazon.factories.sync.rule_sync import (
    AmazonPropertyRuleItemSyncFactory,
    AmazonProductTypeAsinSyncFactory,
)
from sales_channels.integrations.amazon.factories.sync.select_value_sync import (
    AmazonPropertySelectValuesSyncFactory,
)


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


@receiver(post_create, sender='amazon.AmazonProductType')
@receiver(post_update, sender='amazon.AmazonProductType')
def sales_channels__amazon_product_type__ensure_asin(sender, instance, **kwargs):
    signal = kwargs.get('signal')
    if signal == post_update and not instance.is_dirty_field('local_instance', check_relationship=True):
        return

    sync_factory = AmazonProductTypeAsinSyncFactory(instance)
    sync_factory.run()
