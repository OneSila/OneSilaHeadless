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
from sales_channels.integrations.ebay.models import EbaySalesChannel
from sales_channels.models import SalesChannelViewAssign


class EbayChannelAddTask(ChannelScopedAddTask):
    sales_channel_class = EbaySalesChannel


class EbayMarketplaceViewAddTask(ViewScopedAddTask, EbayChannelAddTask):
    view_assign_model = SalesChannelViewAssign

    def build_task_kwargs(self, *, target):
        task_kwargs = super().build_task_kwargs(target=target)
        view_id = getattr(target.sales_channel_view, "id", target.sales_channel_view)
        if view_id:
            task_kwargs["sales_channel_view_id"] = view_id
            task_kwargs["view_id"] = view_id
        return task_kwargs


class EbayNonLiveMarketplaceViewAddTask(EbayMarketplaceViewAddTask):
    live = False


class EbaySingleViewAddTask(SingleViewAddTask, EbayChannelAddTask):
    pass


class EbayProductContentAddTask(ProductContentAddTask, EbayNonLiveMarketplaceViewAddTask):
    pass


class EbayProductPriceAddTask(ProductPriceAddTask, EbayNonLiveMarketplaceViewAddTask):
    pass


class EbayProductImagesAddTask(ProductImagesAddTask, EbayNonLiveMarketplaceViewAddTask):
    pass


class EbayProductPropertyAddTask(ProductPropertyAddTask, EbayNonLiveMarketplaceViewAddTask):
    pass


class EbayProductUpdateAddTask(ProductUpdateAddTask, EbayNonLiveMarketplaceViewAddTask):
    pass


class EbayProductEanCodeAddTask(ProductEanCodeAddTask, EbayNonLiveMarketplaceViewAddTask):
    pass
