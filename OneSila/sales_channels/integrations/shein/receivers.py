from core.receivers import receiver
from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.signals import refresh_website_pull_models, sales_channel_created

from sales_channels.integrations.shein.flows.internal_properties import (
    ensure_internal_properties_flow,
)


@receiver(refresh_website_pull_models, sender='sales_channels.SalesChannel')
@receiver(refresh_website_pull_models, sender='shein.SheinSalesChannel')
@receiver(sales_channel_created, sender='sales_channels.SalesChannel')
@receiver(sales_channel_created, sender='shein.SheinSalesChannel')
def sales_channels__shein__handle_pull(sender, instance, **kwargs):
    real_instance = instance.get_real_instance()
    if not isinstance(real_instance, SheinSalesChannel):
        return

    from sales_channels.integrations.shein.factories.sales_channels import (
        SheinMarketplacePullFactory,
    )

    SheinMarketplacePullFactory(sales_channel=instance).run()
    ensure_internal_properties_flow(real_instance)
