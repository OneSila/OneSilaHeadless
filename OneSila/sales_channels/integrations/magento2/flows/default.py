from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.models import RemoteProduct
from sales_channels.tasks import add_task_to_queue
from sales_channels.helpers import get_import_path


def run_generic_magento_task_flow(task_func, multi_tenant_company, number_of_remote_requests=None, sales_channels_filter_kwargs=None, **kwargs):
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

    for sales_channel in MagentoSalesChannel.objects.filter(**sales_channels_filter_kwargs):

        task_kwargs = {
            'sales_channel_id': sales_channel.id,
            **kwargs
        }

        add_task_to_queue(
            sales_channel_id=sales_channel.id,
            task_func_path=get_import_path(task_func),
            task_kwargs=task_kwargs,
            number_of_remote_requests=number_of_remote_requests
        )

def run_product_specific_magento_task_flow(
    task_func,
    multi_tenant_company,
    product,
    number_of_remote_requests=None,
    sales_channels_filter_kwargs=None,
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
    for sales_channel in MagentoSalesChannel.objects.filter(**sales_channels_filter_kwargs):

        # Queue a task for each remote product
        for remote_product in  RemoteProduct.objects.filter(local_instance=product,sales_channel=sales_channel).iterator():
            task_kwargs = {
                'sales_channel_id': sales_channel.id,
                'remote_product_id': remote_product.id,
                **kwargs
            }

            add_task_to_queue(
                sales_channel_id=sales_channel.id,
                task_func_path=get_import_path(task_func),
                task_kwargs=task_kwargs,
                number_of_remote_requests=number_of_remote_requests
            )


def run_delete_generic_magento_task_flow(task_func, local_instance_id, remote_class, multi_tenant_company, number_of_remote_requests=None, sales_channels_filter_kwargs=None, **kwargs):
    """
    Queues the specified task for each active Magento sales channel,
    passing additional kwargs as needed.

    :param task_func: The task function to be queued.
    :param remote_class: Class of the remote object that needs to be deleted.
    :param kwargs: Additional keyword arguments to pass to the task.
    """
    if sales_channels_filter_kwargs is None:
        sales_channels_filter_kwargs = {'active': True, 'multi_tenant_company': multi_tenant_company}
    else:
        if 'active' not in sales_channels_filter_kwargs:
            sales_channels_filter_kwargs['active'] = True

        sales_channels_filter_kwargs['multi_tenant_company'] = multi_tenant_company

    for sales_channel in MagentoSalesChannel.objects.filter(**sales_channels_filter_kwargs):
        try:
            remote_instance = remote_class.objects.get(local_instance_id=local_instance_id, sales_channel=sales_channel)

            task_kwargs = {
                'sales_channel_id': sales_channel.id,
                'remote_instance': remote_instance.id
            }

            add_task_to_queue(
                sales_channel_id=sales_channel.id,
                task_func_path=get_import_path(task_func),
                task_kwargs=task_kwargs,
                number_of_remote_requests=number_of_remote_requests
            )
        except remote_class.DoesNotExist:
            pass



def run_delete_product_specific_generic_magento_task_flow(
    task_func,
    remote_class,
    multi_tenant_company,
    local_instance_id,
    product,
    sales_channels_filter_kwargs=None,
    number_of_remote_requests=None,
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
    sales_channels = MagentoSalesChannel.objects.filter(**sales_channels_filter_kwargs)

    for sales_channel in sales_channels:
            for remote_product in RemoteProduct.objects.filter(local_instance=product, sales_channel=sales_channel).iterator():
                try:
                    remote_instance = remote_class.objects.get(local_instance_id=local_instance_id, sales_channel=sales_channel, remote_product_id=remote_product_id)


                    task_kwargs = {
                        'sales_channel_id': sales_channel.id,
                        'remote_instance_id': remote_instance.id,
                        'remote_product_id': remote_product.id
                        **kwargs
                    }

                    add_task_to_queue(
                        sales_channel_id=sales_channel.id,
                        task_func_path=get_import_path(task_func),
                        task_kwargs=task_kwargs,
                        number_of_remote_requests=number_of_remote_requests,
                    )
                except remote_class.DoesNotExist:
                    # If the remote instance does not exist for this sales channel, skip
                    pass