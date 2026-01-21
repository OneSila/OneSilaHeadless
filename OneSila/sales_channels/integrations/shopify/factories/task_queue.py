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
from sales_channels.integrations.shopify.models import (
    ShopifyImageProductAssociation,
    ShopifyProduct,
    ShopifyProductProperty,
    ShopifySalesChannel,
)


class ShopifyChannelAddTask(ChannelScopedAddTask):
    sales_channel_class = ShopifySalesChannel


class ShopifySingleChannelAddTask(SingleChannelAddTask, ShopifyChannelAddTask):
    pass


class ShopifyDeleteScopedAddTask(DeleteScopedAddTask, ShopifyChannelAddTask):
    pass


class ShopifySingleChannelDeleteAddTask(DeleteScopedAddTask, ShopifySingleChannelAddTask):
    pass


class ShopifyProductContentAddTask(ProductContentAddTask, ShopifyChannelAddTask):
    pass


class ShopifyProductEanCodeAddTask(ProductEanCodeAddTask, ShopifyChannelAddTask):
    pass


class ShopifyProductImagesAddTask(ProductImagesAddTask, ShopifyChannelAddTask):
    pass


class ShopifyProductPriceAddTask(ProductPriceAddTask, ShopifyChannelAddTask):
    pass


class ShopifyProductPropertyAddTask(ProductPropertyAddTask, ShopifyChannelAddTask):
    # @TODO: Guard against the SHOPIFY_TAG update
    pass


class ShopifyProductUpdateAddTask(ProductUpdateAddTask, ShopifyChannelAddTask):
    pass


class ShopifyProductFullSyncAddTask(ProductFullSyncAddTask, ShopifyChannelAddTask):
    pass


class ShopifyRemoteProductFullSyncAddTask(ShopifyProductFullSyncAddTask, ShopifySingleChannelAddTask):
    pass


class ShopifyProductDeleteAddTask(ShopifyDeleteScopedAddTask):
    remote_class = ShopifyProduct


class ShopifyProductDeleteFromAssignAddTask(ShopifySingleChannelDeleteAddTask):
    remote_class = ShopifyProduct


class ShopifyProductPropertyDeleteAddTask(ProductDeleteScopedAddTask, ShopifyChannelAddTask):
    remote_class = ShopifyProductProperty


class ShopifyImageAssociationDeleteAddTask(ProductDeleteScopedAddTask, ShopifyChannelAddTask):
    remote_class = ShopifyImageProductAssociation
