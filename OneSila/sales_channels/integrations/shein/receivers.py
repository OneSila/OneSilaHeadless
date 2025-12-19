from core.receivers import receiver
from core.signals import post_create, post_update
from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.signals import (
    create_remote_product,
    manual_sync_remote_product,
    refresh_website_pull_models,
    sales_channel_created,
)

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

    from sales_channels.integrations.shein.factories.sales_channels import  SheinSalesChannelViewPullFactory

    SheinSalesChannelViewPullFactory(sales_channel=instance).run()
    ensure_internal_properties_flow(real_instance)


@receiver(post_create, sender='shein.SheinProductCategory')
@receiver(post_update, sender='shein.SheinProductCategory')
def shein__product_category__propagate_to_variations(sender, instance, **kwargs):
    """
    When a Shein category is assigned to a configurable (parent) product,
    automatically propagate it to all its variations.
    """
    from sales_channels.integrations.shein.models import SheinProductCategory

    if not instance.product.is_configurable():
        return

    variations = instance.product.get_configurable_variations(active_only=False)
    for variation in variations:
        SheinProductCategory.objects.get_or_create(
            multi_tenant_company=instance.multi_tenant_company,
            product=variation,
            sales_channel=instance.sales_channel,
            defaults={
                "remote_id": instance.remote_id,
                "site_remote_id": instance.site_remote_id,
            },
        )


@receiver(manual_sync_remote_product, sender='sales_channels.RemoteProduct')
def shein__product__manual_sync(
    sender,
    instance,
    view=None,
    **kwargs,
):
    product = getattr(instance, "local_instance", None)
    if product is None:
        return

    if view is None:
        return

    resolved_view = view.get_real_instance()
    if resolved_view is None:
        return
    sales_channel = resolved_view.sales_channel.get_real_instance()

    from sales_channels.integrations.shein.flows.tasks_runner import (
        run_single_shein_product_task_flow,
    )
    from sales_channels.integrations.shein.tasks import resync_shein_product_db_task

    if not isinstance(sales_channel, SheinSalesChannel) or not sales_channel.active:
        return

    count = 1 + getattr(product, 'get_configurable_variations', lambda: [])().count()

    run_single_shein_product_task_flow(
        task_func=resync_shein_product_db_task,
        view=resolved_view,
        number_of_remote_requests=count,
        product_id=product.id,
        remote_product_id=instance.id,
    )


@receiver(manual_sync_remote_product, sender="shein.SheinProduct")
def shein__shein_product__manual_sync(
    sender,
    instance,
    view=None,
    **kwargs,
):
    # Delegate to the generic receiver for backwards compatibility.
    return shein__product__manual_sync(
        sender=sender,
        instance=instance,
        view=view,
        **kwargs,
    )

@receiver(create_remote_product, sender='sales_channels.SalesChannelViewAssign')
def shein__product__create_from_assign(sender, instance, view, **kwargs):
    sales_channel = instance.sales_channel.get_real_instance()

    from sales_channels.integrations.shein.flows.tasks_runner import (
        run_single_shein_product_task_flow,
    )
    from sales_channels.integrations.shein.models import SheinSalesChannel
    from sales_channels.integrations.shein.tasks import create_shein_product_db_task

    if not isinstance(sales_channel, SheinSalesChannel) or not sales_channel.active:
        return

    resolved_view = view.get_real_instance()
    if resolved_view is None:
        return
    product = instance.product
    count = 1 + getattr(product, 'get_configurable_variations', lambda: [])().count()

    run_single_shein_product_task_flow(
        task_func=create_shein_product_db_task,
        view=resolved_view,
        number_of_remote_requests=count,
        product_id=product.id,
    )
