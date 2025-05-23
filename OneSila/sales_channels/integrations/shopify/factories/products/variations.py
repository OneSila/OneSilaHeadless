from sales_channels.factories.products.variations import (
    RemoteProductVariationAddFactory,
    RemoteProductVariationDeleteFactory
)
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models.products import ShopifyProduct


class ShopifyProductVariationAddFactory(GetShopifyApiMixin, RemoteProductVariationAddFactory):
    """
    Shopify-specific factory for adding a variant to an existing product.
    Delegates initial creation logic to the standard product-create factory.
    """
    remote_model_class = ShopifyProduct

    @property
    def create_factory_class(self):
        from sales_channels.integrations.shopify.factories.products.products import ShopifyProductCreateFactory
        return ShopifyProductCreateFactory
