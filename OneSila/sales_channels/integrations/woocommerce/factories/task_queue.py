from sales_channels.factories.task_queue import (
    ChannelScopedAddTask,
    DeleteScopedAddTask,
    ProductContentAddTask,
    ProductDeleteScopedAddTask,
    ProductEanCodeAddTask,
    ProductFullSyncAddTask,
    ProductImagesAddTask,
    ProductPriceAddTask,
    ProductPropertyAddTask,
    ProductUpdateAddTask,
    SingleChannelAddTask,
)
from sales_channels.integrations.woocommerce.models import (
    WoocommerceMediaThroughProduct,
    WoocommerceProduct,
    WoocommerceProductProperty,
    WoocommerceSalesChannel,
)


class WooCommerceChannelAddTask(ChannelScopedAddTask):
    sales_channel_class = WoocommerceSalesChannel


class WooCommerceSingleChannelAddTask(SingleChannelAddTask, WooCommerceChannelAddTask):
    pass


class WooCommerceDeleteScopedAddTask(DeleteScopedAddTask, WooCommerceChannelAddTask):
    pass


class WooCommerceSingleChannelDeleteAddTask(DeleteScopedAddTask, WooCommerceSingleChannelAddTask):
    pass


class WooCommerceProductContentAddTask(ProductContentAddTask, WooCommerceChannelAddTask):
    pass


class WooCommerceProductEanCodeAddTask(ProductEanCodeAddTask, WooCommerceChannelAddTask):
    pass


class WooCommerceProductImagesAddTask(ProductImagesAddTask, WooCommerceChannelAddTask):
    pass


class WooCommerceProductPriceAddTask(ProductPriceAddTask, WooCommerceChannelAddTask):
    pass


class WooCommerceProductPropertyAddTask(ProductPropertyAddTask, WooCommerceChannelAddTask):
    pass


class WooCommerceProductUpdateAddTask(ProductUpdateAddTask, WooCommerceChannelAddTask):
    pass


class WooCommerceProductFullSyncAddTask(ProductFullSyncAddTask, WooCommerceChannelAddTask):
    pass


class WooCommerceRemoteProductFullSyncAddTask(ProductFullSyncAddTask, WooCommerceSingleChannelAddTask):
    pass

class WooCommerceProductDeleteAddTask(WooCommerceDeleteScopedAddTask):
    remote_class = WoocommerceProduct


class WooCommerceProductDeleteFromAssignAddTask(WooCommerceSingleChannelDeleteAddTask):
    remote_class = WoocommerceProduct


class WooCommerceProductPropertyDeleteAddTask(ProductDeleteScopedAddTask, WooCommerceChannelAddTask):
    remote_class = WoocommerceProductProperty


class WooCommerceImageAssociationDeleteAddTask(ProductDeleteScopedAddTask, WooCommerceChannelAddTask):
    remote_class = WoocommerceMediaThroughProduct
