from sales_channels.models.products import (
    RemoteProduct,
    RemotePrice,
    RemoteProductContent,
    RemoteImageProductAssociation,
    RemoteCategory,
    RemoteEanCode,
)


class ShopifyProduct(RemoteProduct):
    """
    Shopify-specific model for remote products, inheriting from the general RemoteProduct.
    """
    pass


class ShopifyPrice(RemotePrice):
    """
    Shopify-specific model for remote prices (per-variant prices live on the variant),
    inheriting from the general RemotePrice.
    """
    pass


class ShopifyProductContent(RemoteProductContent):
    """
    Shopify-specific model for remote product content/localization.
    """
    pass


class ShopifyImageProductAssociation(RemoteImageProductAssociation):
    """
    Shopify-specific model for associating images with remote products.
    """
    pass


class ShopifyCollection(RemoteCategory):
    """
    Shopify-specific model for remote collections (categories).
    """
    pass


class ShopifyEanCode(RemoteEanCode):
    """
    Shopify-specific model for remote EAN codes.
    """
    class Meta:
        verbose_name = 'Shopify EAN Code'
        verbose_name_plural = 'Shopify EAN Codes'