from sales_channels.factories.task_queue import (
    ChannelScopedAddTask,
    DeleteScopedAddTask,
    GuardResult,
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
    def guard(self, *, target):
        guard_result = super().guard(target=target)
        if not guard_result.allowed:
            return guard_result

        from sales_channels.integrations.shopify.constants import SHOPIFY_TAGS

        product_property = self.local_instance
        property_obj = getattr(product_property, "property", None) if product_property else None
        if property_obj and property_obj.internal_name == SHOPIFY_TAGS:
            return GuardResult(allowed=False, reason="shopify_tags_guard")

        return guard_result


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
