from core.receivers import receiver
from sales_channels.signals import refresh_website_pull_models, sales_channel_created
from sales_channels.integrations.ebay.models import EbaySalesChannel

# @receiver(post_update, sender='app_name.Model')
# def app_name__model__action__example(sender, instance, **kwargs):
#     do_something()
@receiver(refresh_website_pull_models, sender='sales_channels.SalesChannel')
@receiver(refresh_website_pull_models, sender='ebay.EbaySalesChannel')
@receiver(sales_channel_created, sender='sales_channels.SalesChannel')
@receiver(sales_channel_created, sender='ebay.EbaySalesChannel')
def sales_channels__ebay__handle_pull(sender, instance, **kwargs):
    from sales_channels.integrations.ebay.factories.sales_channels import (
        EbaySalesChannelViewPullFactory,
        EbayRemoteLanguagePullFactory,
        EbayRemoteCurrencyPullFactory,
    )

    if not isinstance(instance.get_real_instance(), EbaySalesChannel):
        return

    views_factory = EbaySalesChannelViewPullFactory(sales_channel=instance)
    views_factory.run()

    languages_factory = EbayRemoteLanguagePullFactory(sales_channel=instance)
    languages_factory.run()

    currencies_factory = EbayRemoteCurrencyPullFactory(sales_channel=instance)
    currencies_factory.run()
