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


class ShopifyProductVariationDeleteFactory(GetShopifyApiMixin, RemoteProductVariationDeleteFactory):
    """
    Shopify-specific factory for deleting a product variant via REST.
    """

    def delete_remote(self):
        # Attempt to fetch the variant by its remote_id
        variant = self.api.Variant.find(self.remote_instance.remote_id)
        if not variant:
            # Already deleted or never existed
            return True
        # Destroy the variant
        return variant.destroy()

    def serialize_response(self, response):
        # Shopify .destroy() returns True/False
        return response
