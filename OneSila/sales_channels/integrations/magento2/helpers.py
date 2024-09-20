from sales_channels.integrations.magento2.models import MagentoSalesChannel


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