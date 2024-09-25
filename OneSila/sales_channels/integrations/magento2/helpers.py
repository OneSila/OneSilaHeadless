from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.models import RemoteProduct


def run_generic_magento_factory(sales_channel_id, factory_class, local_instance_id=None, local_instance_class=None, factory_kwargs=None):
    sales_channel = MagentoSalesChannel.objects.get(id=sales_channel_id)

    local_instance = None
    if local_instance_class and local_instance_id:
        local_instance = local_instance_class.objects.get(id=local_instance_id)


    if factory_kwargs is None:
        factory_kwargs = {}

    factory_kwargs.update({'sales_channel': sales_channel, 'local_instance': local_instance})

    factory = factory_class(**factory_kwargs)
    factory.run()

def run_remote_product_dependent_magento_factory(
    sales_channel_id,
    factory_class,
    local_instance_id=None,
    local_instance_class=None,
    remote_product_id=None,
    factory_kwargs=None
):
    """
    Executes a generic Magento factory task with the provided parameters.

    :param sales_channel_id: ID of the sales channel.
    :param factory_class: The factory class to instantiate and run.
    :param local_instance_id: ID of the local instance (optional).
    :param local_instance_class: Class of the local instance (optional).
    :param remote_product_id: ID of the remote product (optional).
    :param factory_kwargs: Additional keyword arguments for the factory (optional).
    """
    sales_channel = MagentoSalesChannel.objects.get(id=sales_channel_id)

    # Retrieve the remote product if remote_product_id is provided
    remote_product = None
    if remote_product_id:
        remote_product = RemoteProduct.objects.get(id=remote_product_id)
        if remote_product.sales_channel_id != sales_channel_id:
            raise ValueError("The remote product does not belong to the provided sales channel.")

    # Retrieve the local instance
    if local_instance_class and local_instance_id:
        local_instance = local_instance_class.objects.get(id=local_instance_id)
    elif remote_product:
        local_instance = remote_product.local_instance
    else:
        local_instance = None

    if factory_kwargs is None:
        factory_kwargs = {}

    # Update factory_kwargs with the retrieved instances
    factory_kwargs.update({
        'sales_channel': sales_channel,
        'local_instance': local_instance,
        'remote_product': remote_product,
    })

    factory = factory_class(**factory_kwargs)
    factory.run()
