from huey.contrib.djhuey import db_task
from core.huey import HIGH_PRIORITY, LOW_PRIORITY, MEDIUM_PRIORITY, CRUCIAL_PRIORITY
from properties.models import Property, PropertySelectValue, ProductPropertiesRule
from sales_channels.decorators import remote_task
from sales_channels.factories.remote_task import BaseRemoteTask
from sales_channels.integrations.magento2.factories.properties.properties import MagentoPropertyUpdateFactory
from sales_channels.integrations.magento2.models import MagentoSalesChannel

def run_generic_factory(sales_channel_id, factory_class, local_instance_id=None, local_instance_class=None, factory_kwargs=None):
    sales_channel = MagentoSalesChannel.objects.get(id=sales_channel_id)

    local_instance = None
    if local_instance_class and local_instance_id:
        local_instance = local_instance_class.objects.get(id=local_instance_id)


    if factory_kwargs is None:
        factory_kwargs = {}

    factory_kwargs.update({'sales_channel': sales_channel, 'local_instance': local_instance})

    factory = factory_class(**factory_kwargs)
    factory.run()

# !IMPORTANT: @remote_task needs to be above in order to work
@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_magento_property_db_task(task_queue_item_id, sales_channel_id, property_id):
    from .factories.properties.properties import MagentoPropertyCreateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_generic_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoPropertyCreateFactory,
            local_instance_id=property_id,
            local_instance_class=Property
        )

    task.execute(actual_task)


@remote_task(number_of_remote_requests=3)
@db_task()
def update_magento_property_db_task(task_queue_item_id, sales_channel_id, property_id):
    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_generic_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoPropertyUpdateFactory,
            local_instance_id=property_id,
            local_instance_class=Property
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=2)
@db_task()
def delete_magento_property_db_task(task_queue_item_id, sales_channel_id, remote_instance_id):
    from .factories.properties.properties import MagentoPropertyDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)
    def actual_task():
        sales_channel = MagentoSalesChannel.objects.get(id=sales_channel_id)

        factory_kwargs = {'remote_instance_id': remote_instance_id, 'sales_channel': sales_channel}
        factory = MagentoPropertyDeleteFactory(**factory_kwargs)
        factory.run()

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_magento_property_select_value_task(task_queue_item_id, sales_channel_id, property_select_value_id):
    from .factories.properties.properties import MagentoPropertySelectValueCreateFactory

    task = BaseRemoteTask(task_queue_item_id)
    def actual_task():
        run_generic_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoPropertySelectValueCreateFactory,
            local_instance_id=property_select_value_id,
            local_instance_class=PropertySelectValue
        )

    task.execute(actual_task)


@remote_task(number_of_remote_requests=3)
@db_task()
def update_magento_property_select_value_task(task_queue_item_id, sales_channel_id, property_select_value_id):
    from .factories.properties.properties import MagentoPropertySelectValueUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)
    def actual_task():
        run_generic_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoPropertySelectValueUpdateFactory,
            local_instance_id=property_select_value_id,
            local_instance_class=PropertySelectValue
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=2)
@db_task()
def delete_magento_property_select_value_task(task_queue_item_id, sales_channel_id, remote_instance_id):
    from .factories.properties.properties import MagentoPropertySelectValueDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)
    def actual_task():
        sales_channel = MagentoSalesChannel.objects.get(id=sales_channel_id)

        factory_kwargs = {'remote_instance_id': remote_instance_id, 'sales_channel': sales_channel}
        factory = MagentoPropertySelectValueDeleteFactory(**factory_kwargs)
        factory.run()

    task.execute(actual_task)


@remote_task(priority=LOW_PRIORITY, number_of_remote_requests=2)
@db_task()
def pull_magento_sales_channel_views_task(task_queue_item_id, sales_channel_id):
    """
    Task to run the SalesChannelViewPullFactory for a given SalesChannel.
    """
    from .factories.sales_channels.views import MagentoSalesChannelViewPullFactory

    task = BaseRemoteTask(task_queue_item_id)
    def actual_task():
        sales_channel = MagentoSalesChannel.objects.get(id=sales_channel_id)
        factory = MagentoSalesChannelViewPullFactory(sales_channel=sales_channel)
        factory.run()

    task.execute(actual_task)

@remote_task(priority=LOW_PRIORITY,number_of_remote_requests=2)
@db_task()
def pull_magento_languages_task(task_queue_item_id, sales_channel_id):
    """
    Task to run the MagentoRemoteLanguage for a given SalesChannel.
    """
    from .factories.sales_channels.languages import MagentoRemoteLanguagePullFactory

    task = BaseRemoteTask(task_queue_item_id)
    def actual_task():
        sales_channel = MagentoSalesChannel.objects.get(id=sales_channel_id)
        factory = MagentoRemoteLanguagePullFactory(sales_channel=sales_channel)
        factory.run()

    task.execute(actual_task)


@remote_task(priority=HIGH_PRIORITY)
@db_task()
def create_magento_attribute_set_task(task_queue_item_id, sales_channel_id, rule_id):
    from .factories.properties.properties import MagentoAttributeSetCreateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_generic_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoAttributeSetCreateFactory,
            local_instance_id=rule_id,
            local_instance_class=ProductPropertiesRule
        )

    task.execute(actual_task)

@remote_task(priority=HIGH_PRIORITY)
@db_task()
def update_magento_attribute_set_task(task_queue_item_id, sales_channel_id, rule_id, update_name_only=False):
    from .factories.properties.properties import MagentoAttributeSetUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        factory_kwargs = {'update_name_only': update_name_only}

        run_generic_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoAttributeSetUpdateFactory,
            local_instance_id=rule_id,
            local_instance_class=ProductPropertiesRule,
            factory_kwargs=factory_kwargs
        )

    task.execute(actual_task)

@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=2)
@db_task()
def delete_magento_attribute_set_task(task_queue_item_id, sales_channel_id, remote_instance_id):
    from .factories.properties.properties import MagentoAttributeSetDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        sales_channel = MagentoSalesChannel.objects.get(id=sales_channel_id)

        factory_kwargs = {'remote_instance_id': remote_instance_id, 'sales_channel': sales_channel}
        factory = MagentoAttributeSetDeleteFactory(**factory_kwargs)
        factory.run()

    task.execute(actual_task)


@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_magento_order_status_db_task(task_queue_item_id, sales_channel_id, order_id):
    from .factories.orders.orders import MagentoChangeRemoteOrderStatus
    from orders.models import Order

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_generic_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoChangeRemoteOrderStatus,
            local_instance_id=order_id,
            local_instance_class=Order
        )

    task.execute(actual_task)