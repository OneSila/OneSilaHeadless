from sales_channels.factories.task_queue import (
    ChannelScopedAddTask,
    ProductContentAddTask,
    ProductEanCodeAddTask,
    ProductImagesAddTask,
    ProductPriceAddTask,
    ProductPropertyAddTask,
    ProductUpdateAddTask,
    SingleChannelAddTask,
)
from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.integrations.shein.tasks import resync_shein_product_db_task


class SheinChannelAddTask(ChannelScopedAddTask):
    sales_channel_class = SheinSalesChannel


class SheinSingleChannelAddTask(SingleChannelAddTask, SheinChannelAddTask):
    pass


class SheinNonLiveChannelAddTask(SheinChannelAddTask):
    live = False
    product_task_fallback = resync_shein_product_db_task


class SheinProductContentAddTask(ProductContentAddTask, SheinNonLiveChannelAddTask):
    pass


class SheinProductPriceAddTask(ProductPriceAddTask, SheinNonLiveChannelAddTask):
    pass


class SheinProductImagesAddTask(ProductImagesAddTask, SheinNonLiveChannelAddTask):
    pass


class SheinProductPropertyAddTask(ProductPropertyAddTask, SheinNonLiveChannelAddTask):
    pass


class SheinProductUpdateAddTask(ProductUpdateAddTask, SheinNonLiveChannelAddTask):
    pass


class SheinProductEanCodeAddTask(ProductEanCodeAddTask, SheinNonLiveChannelAddTask):
    pass
