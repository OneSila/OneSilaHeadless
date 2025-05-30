from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.models import RemoteProduct
from integrations.tasks import add_task_to_queue
from integrations.helpers import get_import_path
from django.db import transaction


def run_generic_sales_channel_task_flow(task_func, multi_tenant_company, number_of_remote_requests=None, sales_channels_filter_kwargs=None, sales_channel_class=MagentoSalesChannel, **kwargs):
    """
    Queues the specified task for each active Magento sales channel,
    passing additional kwargs as needed.

    :param task_func: The task function to be queued.
    :param number_of_remote_requests: Manually giving the number of requests by the task
    :param kwargs: Additional keyword arguments to pass to the task.
    """
    if sales_channels_filter_kwargs is None:
        sales_channels_filter_kwargs = {'active': True, 'multi_tenant_company': multi_tenant_company}
    else:
        if 'active' not in sales_channels_filter_kwargs:
            sales_channels_filter_kwargs['active'] = True
            sales_channels_filter_kwargs['multi_tenant_company'] = multi_tenant_company

    for sales_channel in sales_channel_class.objects.filter(**sales_channels_filter_kwargs):

        task_kwargs = {
            'sales_channel_id': sales_channel.id,
            **kwargs
        }

        transaction.on_commit(lambda: add_task_to_queue(
            integration_id=sales_channel.id,
            task_func_path=get_import_path(task_func),
            task_kwargs=task_kwargs,
            number_of_remote_requests=number_of_remote_requests
        ))


def run_product_specific_sales_channel_task_flow(
    task_func,
    multi_tenant_company,
    product,
    number_of_remote_requests=None,
    sales_channels_filter_kwargs=None,
    sales_channel_class=MagentoSalesChannel,
    **kwargs
):
    """
    Queues the specified task for each active Magento sales channel and associated RemoteProduct for the given product,
    passing additional kwargs as needed.

    :param task_func: The task function to be queued.
    :param product: The local product instance to filter RemoteProducts.
    :param multi_tenant_company: The company instance for multi-tenancy.
    :param number_of_remote_requests: Manually specify the number of requests made by the task.
    :param sales_channels_filter_kwargs: Additional filters for sales channels.
    :param kwargs: Additional keyword arguments to pass to the task.
    """
    if sales_channels_filter_kwargs is None:
        sales_channels_filter_kwargs = {
            'active': True,
            'multi_tenant_company': multi_tenant_company
        }
    else:
        if 'active' not in sales_channels_filter_kwargs:
            sales_channels_filter_kwargs['active'] = True

        sales_channels_filter_kwargs['multi_tenant_company'] = multi_tenant_company

    # Iterate over each active sales channel
    for sales_channel in sales_channel_class.objects.filter(**sales_channels_filter_kwargs):

        # Queue a task for each remote product
        for remote_product in RemoteProduct.objects.filter(local_instance=product, sales_channel=sales_channel).iterator():
            task_kwargs = {
                'sales_channel_id': sales_channel.id,
                'remote_product_id': remote_product.id,
                **kwargs
            }

            transaction.on_commit(lambda: add_task_to_queue(
                integration_id=sales_channel.id,
                task_func_path=get_import_path(task_func),
                task_kwargs=task_kwargs,
                number_of_remote_requests=number_of_remote_requests
            ))


def run_delete_generic_sales_channel_task_flow(
        task_func,
        local_instance_id,
        remote_class,
        multi_tenant_company,
        number_of_remote_requests=None,
        sales_channels_filter_kwargs=None,
        is_variation=False,  # for products if a delete comes from a variation
        is_multiple=False,   # if True, process multiple remote objects using filter()
        sales_channel_class=MagentoSalesChannel,
        **kwargs):
    """
    Queues the specified task for each active Magento sales channel,
    passing additional kwargs as needed.

    :param task_func: The task function to be queued.
    :param remote_class: Class of the remote object that needs to be deleted.
    :param number_of_remote_requests: Number of remote requests to include with the task.
    :param sales_channels_filter_kwargs: Additional filters for selecting Magento sales channels.
    :param is_variation: Boolean flag for variations (if True, force is_variation to False when fetching).
    :param is_multiple: If True, use .filter() to retrieve all matching remote instances and queue a task for each.
    :param kwargs: Additional keyword arguments to pass to the task.
    """
    if sales_channels_filter_kwargs is None:
        sales_channels_filter_kwargs = {'active': True, 'multi_tenant_company': multi_tenant_company}
    else:
        if 'active' not in sales_channels_filter_kwargs:
            sales_channels_filter_kwargs['active'] = True
        sales_channels_filter_kwargs['multi_tenant_company'] = multi_tenant_company

    def queue_task(sales_channel, remote_instance):
        task_kwargs = {
            'sales_channel_id': sales_channel.id,
            'remote_instance': remote_instance.id
        }

        transaction.on_commit(lambda: add_task_to_queue(
            integration_id=sales_channel.id,
            task_func_path=get_import_path(task_func),
            task_kwargs=task_kwargs,
            number_of_remote_requests=number_of_remote_requests
        ))

    for sales_channel in sales_channel_class.objects.filter(**sales_channels_filter_kwargs):
        get_kwargs = {
            "local_instance_id": local_instance_id,
            "sales_channel": sales_channel
        }
        # For variations, force is_variation to False (as per your note)
        if is_variation:
            get_kwargs['is_variation'] = False

        try:
            if is_multiple:
                remote_instances = remote_class.objects.filter(**get_kwargs)
                for remote_instance in remote_instances:
                    queue_task(sales_channel, remote_instance)
            else:
                remote_instance = remote_class.objects.get(**get_kwargs)
                queue_task(sales_channel, remote_instance)
        except remote_class.DoesNotExist:
            pass


def run_delete_product_specific_generic_sales_channel_task_flow(
    task_func,
    remote_class,
    multi_tenant_company,
    local_instance_id,
    product,
    sales_channels_filter_kwargs=None,
    number_of_remote_requests=None,
    sales_channel_class=MagentoSalesChannel,
    **kwargs
):
    """
    Queues the specified task for each active Magento sales channel,
    passing additional kwargs as needed.

    :param task_func: The task function to be queued.
    :param remote_class: Class of the remote object that needs to be deleted.
    :param kwargs: Additional keyword arguments to pass to the task.
    """

    if sales_channels_filter_kwargs is None:
        sales_channels_filter_kwargs = {
            'active': True,
            'multi_tenant_company': multi_tenant_company
        }
    else:
        if 'active' not in sales_channels_filter_kwargs:
            sales_channels_filter_kwargs['active'] = True

        sales_channels_filter_kwargs['multi_tenant_company'] = multi_tenant_company

    # Fetch the relevant sales channels
    sales_channels = sales_channel_class.objects.filter(**sales_channels_filter_kwargs)

    for sales_channel in sales_channels:
        for remote_product in RemoteProduct.objects.filter(local_instance=product, sales_channel=sales_channel).iterator():
            try:
                remote_instance = remote_class.objects.get(local_instance_id=local_instance_id,
                                                           sales_channel=sales_channel, remote_product_id=remote_product.id)

                task_kwargs = {
                    'sales_channel_id': sales_channel.id,
                    'remote_instance_id': remote_instance.id,
                    'remote_product_id': remote_product.id
                }

                transaction.on_commit(lambda: add_task_to_queue(
                    integration_id=sales_channel.id,
                    task_func_path=get_import_path(task_func),
                    task_kwargs=task_kwargs,
                    number_of_remote_requests=number_of_remote_requests,
                    **kwargs
                ))

            except remote_class.DoesNotExist:
                # If the remote instance does not exist for this sales channel, skip
                pass
