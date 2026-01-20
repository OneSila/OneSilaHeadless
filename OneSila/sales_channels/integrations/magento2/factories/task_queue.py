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
    RuleScopedAddTask,
    SingleChannelAddTask,
)
from sales_channels.integrations.magento2.models.properties import (
    MagentoAttributeSet,
    MagentoProductProperty,
    MagentoProperty,
    MagentoPropertySelectValue,
)
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.integrations.magento2.models.products import MagentoProduct
from sales_channels.integrations.magento2.models.products import MagentoImageProductAssociation


class MagentoChannelAddTask(ChannelScopedAddTask):
    sales_channel_class = MagentoSalesChannel


class MagentoSingleChannelAddTask(SingleChannelAddTask, MagentoChannelAddTask):
    pass


class MagentoDeleteScopedAddTask(DeleteScopedAddTask, MagentoChannelAddTask):
    pass


class MagentoRuleScopedAddTask(RuleScopedAddTask, MagentoChannelAddTask):
    pass


class MagentoSingleChannelDeleteAddTask(DeleteScopedAddTask, MagentoSingleChannelAddTask):
    pass


class MagentoAttributeSetDeleteAddTask(MagentoDeleteScopedAddTask):
    remote_class = MagentoAttributeSet


class MagentoProductImagesAddTask(ProductImagesAddTask, MagentoChannelAddTask):
    pass


class MagentoProductContentAddTask(ProductContentAddTask, MagentoChannelAddTask):
    pass


class MagentoProductPriceAddTask(ProductPriceAddTask, MagentoChannelAddTask):
    pass


class MagentoProductEanCodeAddTask(ProductEanCodeAddTask, MagentoChannelAddTask):
    pass


class MagentoProductPropertyAddTask(ProductPropertyAddTask, MagentoChannelAddTask):
    pass


class MagentoProductUpdateAddTask(ProductUpdateAddTask, MagentoChannelAddTask):
    pass


class MagentoProductFullSyncAddTask(ProductFullSyncAddTask, MagentoChannelAddTask):
    pass


class MagentoProductPropertyDeleteAddTask(ProductDeleteScopedAddTask, MagentoChannelAddTask):
    remote_class = MagentoProductProperty


class MagentoProductDeleteAddTask(MagentoDeleteScopedAddTask):
    remote_class = MagentoProduct


class MagentoProductDeleteFromAssignAddTask(MagentoSingleChannelDeleteAddTask):
    remote_class = MagentoProduct


class MagentoPropertyDeleteAddTask(MagentoDeleteScopedAddTask):
    remote_class = MagentoProperty


class MagentoPropertySelectValueDeleteAddTask(MagentoDeleteScopedAddTask):
    remote_class = MagentoPropertySelectValue


class MagentoImageAssociationDeleteAddTask(ProductDeleteScopedAddTask, MagentoChannelAddTask):
    remote_class = MagentoImageProductAssociation
