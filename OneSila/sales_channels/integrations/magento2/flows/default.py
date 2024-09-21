from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.tasks import add_task_to_queue
from sales_channels.helpers import get_import_path


def run_generic_magento_task_flow(task_func, number_of_remote_requests=None, sales_channels_filter_kwargs=None, **kwargs):
    """
    Queues the specified task for each active Magento sales channel,
    passing additional kwargs as needed.

    :param task_func: The task function to be queued.
    :param number_of_remote_requests: Manually giving the number of requests by the task
    :param kwargs: Additional keyword arguments to pass to the task.
    """
    if sales_channels_filter_kwargs is None:
        sales_channels_filter_kwargs = {'active': True}
    else:
        if 'active' not in sales_channels_filter_kwargs:
            sales_channels_filter_kwargs['active'] = True

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

def run_delete_generic_magento_task_flow(task_func, remote_class, sales_channels_filter_kwargs=None, **kwargs):
    """
    Queues the specified task for each active Magento sales channel,
    passing additional kwargs as needed.

    :param task_func: The task function to be queued.
    :param remote_class: Class of the remote object that needs to be deleted.
    :param kwargs: Additional keyword arguments to pass to the task.
    """
    local_instance_id = kwargs.get('local_instance_id', None)

    if sales_channels_filter_kwargs is None:
        sales_channels_filter_kwargs = {'active': True}
    else:
        if 'active' not in sales_channels_filter_kwargs:
            sales_channels_filter_kwargs['active'] = True

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
            )
        except remote_class.DoesNotExist:
            pass