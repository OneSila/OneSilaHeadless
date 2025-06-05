from core.receivers import receiver
from core.signals import post_create, post_update
from sales_channels.signals import refresh_website_pull_models, sales_channel_created
from sales_channels.integrations.amazon.models import AmazonSalesChannel


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

# Example placeholder for future signal handlers
# @receiver(post_update, sender='app_name.Model')
# def app_name__model__action__example(sender, instance, **kwargs):
#     do_something()
