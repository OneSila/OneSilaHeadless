from django.db import transaction

from integrations.helpers import get_import_path
from integrations.tasks import add_task_to_queue
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
)
from sales_channels.models import RemoteProduct


def run_product_amazon_sales_channel_task_flow(
    task_func,
    multi_tenant_company,
    product,
    number_of_remote_requests=None,
    sales_channels_filter_kwargs=None,
    **kwargs,
):
    """Queue a task for each combination of sales channel, marketplace and remote product."""
    if sales_channels_filter_kwargs is None:
        sales_channels_filter_kwargs = {
            "active": True,
            "multi_tenant_company": multi_tenant_company,
        }
    else:
        if "active" not in sales_channels_filter_kwargs:
            sales_channels_filter_kwargs["active"] = True
        sales_channels_filter_kwargs["multi_tenant_company"] = multi_tenant_company

    for sales_channel in AmazonSalesChannel.objects.filter(**sales_channels_filter_kwargs):
        for view in AmazonSalesChannelView.objects.filter(sales_channel=sales_channel):
            for remote_product in RemoteProduct.objects.filter(
                local_instance=product,
                sales_channel=sales_channel,
            ).iterator():
                task_kwargs = {
                    "sales_channel_id": sales_channel.id,
                    "sales_channel_view_id": view.id,
                    "view_id": view.id,
                    "remote_product_id": remote_product.id,
                    **kwargs,
                }
                transaction.on_commit(
                    lambda lb_task_kwargs=task_kwargs, integration_id=sales_channel.id: add_task_to_queue(
                        integration_id=integration_id,
                        task_func_path=get_import_path(task_func),
                        task_kwargs=lb_task_kwargs,
                        number_of_remote_requests=number_of_remote_requests,
                    )
                )


def run_delete_product_specific_amazon_sales_channel_task_flow(
    task_func,
    remote_class,
    multi_tenant_company,
    local_instance_id,
    product,
    sales_channels_filter_kwargs=None,
    number_of_remote_requests=None,
    **kwargs,
):
    """Queue a deletion task for each combination of sales channel, marketplace and remote product."""
    if sales_channels_filter_kwargs is None:
        sales_channels_filter_kwargs = {
            "active": True,
            "multi_tenant_company": multi_tenant_company,
        }
    else:
        if "active" not in sales_channels_filter_kwargs:
            sales_channels_filter_kwargs["active"] = True
        sales_channels_filter_kwargs["multi_tenant_company"] = multi_tenant_company

    sales_channels = AmazonSalesChannel.objects.filter(**sales_channels_filter_kwargs)
    for sales_channel in sales_channels:
        for view in AmazonSalesChannelView.objects.filter(sales_channel=sales_channel):
            for remote_product in RemoteProduct.objects.filter(
                local_instance=product, sales_channel=sales_channel
            ).iterator():
                try:
                    remote_instance = remote_class.objects.get(
                        local_instance_id=local_instance_id,
                        sales_channel=sales_channel,
                        remote_product_id=remote_product.id,
                    )
                except remote_class.DoesNotExist:
                    continue

                task_kwargs = {
                    "sales_channel_id": sales_channel.id,
                    "sales_channel_view_id": view.id,
                    "view_id": view.id,
                    "remote_instance_id": remote_instance.id,
                    "remote_product_id": remote_product.id,
                }
                transaction.on_commit(
                    lambda lb_task_kwargs=task_kwargs, integration_id=sales_channel.id: add_task_to_queue(
                        integration_id=integration_id,
                        task_func_path=get_import_path(task_func),
                        task_kwargs=lb_task_kwargs,
                        number_of_remote_requests=number_of_remote_requests,
                        **kwargs,
                    )
                )
