from core.receivers import receiver

from sales_channels.integrations.mirakl.models import MiraklSalesChannel
from sales_channels.signals import refresh_website_pull_models, sales_channel_created


@receiver(refresh_website_pull_models, sender="sales_channels.SalesChannel")
@receiver(refresh_website_pull_models, sender="mirakl.MiraklSalesChannel")
@receiver(sales_channel_created, sender="sales_channels.SalesChannel")
@receiver(sales_channel_created, sender="mirakl.MiraklSalesChannel")
def sales_channels__mirakl__handle_pull(sender, instance, **kwargs):
    real_instance = instance.get_real_instance()
    if not isinstance(real_instance, MiraklSalesChannel):
        return

    if not real_instance.connect():
        return

    from sales_channels.integrations.mirakl.factories.sales_channels import (
        MiraklRemoteCurrencyPullFactory,
        MiraklRemoteLanguagePullFactory,
        MiraklSalesChannelViewPullFactory,
    )

    MiraklSalesChannelViewPullFactory(sales_channel=real_instance).run()
    MiraklRemoteLanguagePullFactory(sales_channel=real_instance).run()
    MiraklRemoteCurrencyPullFactory(sales_channel=real_instance).run()
