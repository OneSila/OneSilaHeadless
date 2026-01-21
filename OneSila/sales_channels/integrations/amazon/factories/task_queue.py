from sales_channels.factories.task_queue import (
    ChannelScopedAddTask,
    ProductContentAddTask,
    ProductEanCodeAddTask,
    ProductImagesAddTask,
    ProductPriceAddTask,
    ProductPropertyAddTask,
    ProductUpdateAddTask,
    SingleViewAddTask,
    ViewScopedAddTask,
)
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.models import SalesChannelViewAssign


class AmazonChannelAddTask(ChannelScopedAddTask):
    sales_channel_class = AmazonSalesChannel


class AmazonMarketplaceViewAddTask(ViewScopedAddTask, AmazonChannelAddTask):
    view_assign_model = SalesChannelViewAssign

    def build_task_kwargs(self, *, target):
        task_kwargs = super().build_task_kwargs(target=target)
        view_id = getattr(target.sales_channel_view, "id", target.sales_channel_view)
        if view_id:
            task_kwargs["sales_channel_view_id"] = view_id
            task_kwargs["view_id"] = view_id
        return task_kwargs


class AmazonNonLiveMarketplaceViewAddTask(AmazonMarketplaceViewAddTask):
    live = False


class AmazonSingleViewAddTask(SingleViewAddTask, AmazonChannelAddTask):
    pass


class AmazonProductContentAddTask(ProductContentAddTask, AmazonNonLiveMarketplaceViewAddTask):
    pass


class AmazonProductPriceAddTask(ProductPriceAddTask, AmazonNonLiveMarketplaceViewAddTask):
    pass


class AmazonProductImagesAddTask(ProductImagesAddTask, AmazonNonLiveMarketplaceViewAddTask):
    pass


class AmazonProductPropertyAddTask(ProductPropertyAddTask, AmazonNonLiveMarketplaceViewAddTask):
    pass


class AmazonProductUpdateAddTask(ProductUpdateAddTask, AmazonNonLiveMarketplaceViewAddTask):
    pass


class AmazonProductEanCodeAddTask(ProductEanCodeAddTask, AmazonNonLiveMarketplaceViewAddTask):
    pass
