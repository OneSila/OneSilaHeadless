from sales_channels.factories.task_queue import ChannelScopedAddTask, SingleChannelAddTask
from sales_channels.integrations.magento2.models import MagentoSalesChannel


class MagentoChannelAddTask(ChannelScopedAddTask):
    sales_channel_class = MagentoSalesChannel


class MagentoSingleChannelAddTask(SingleChannelAddTask, MagentoChannelAddTask):
    pass
