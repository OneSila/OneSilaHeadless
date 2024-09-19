from sales_channels.models.products import (
    RemoteProduct,
    RemoteInventory,
    RemotePrice,
    RemoteProductContent,
    RemoteImageProductAssociation,
    RemoteCategory
)

class MagentoProduct(RemoteProduct):
    """
    Magento-specific model for remote products, inheriting from the general RemoteProduct.
    """
    pass

class MagentoInventory(RemoteInventory):
    """
    Magento-specific model for remote inventory, inheriting from the general RemoteInventory.
    """
    pass

class MagentoPrice(RemotePrice):
    """
    Magento-specific model for remote prices, inheriting from the general RemotePrice.
    """
    pass

class MagentoProductContent(RemoteProductContent):
    """
    Magento-specific model for remote product content, inheriting from the general RemoteProductContent.
    """
    pass

class MagentoImageProductAssociation(RemoteImageProductAssociation):
    """
    Magento-specific model for associating images with remote products.
    Since Magento does not save images in the gallery, this model is specific to Magento's needs.
    """
    pass

class MagentoCategory(RemoteCategory):
    """
    Magento-specific model for remote categories, inheriting from the general RemoteCategory.
    """
    pass
