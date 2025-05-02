from sales_channels.factories.products.images import (
    RemoteMediaProductThroughCreateFactory,
    RemoteMediaProductThroughUpdateFactory,
    RemoteMediaProductThroughDeleteFactory,
    RemoteImageDeleteFactory
)
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models.products import ShopifyImageProductAssociation

class ShopifyMediaProductThroughCreateFactory(GetShopifyApiMixin, RemoteMediaProductThroughCreateFactory):
    """
    Creates a new image on Shopify for a single-variant product.
    """
    remote_model_class = ShopifyImageProductAssociation

    def create_remote_image(self):
        # Session is already active via base run()
        product = self.api.Product.find(self.remote_product.remote_id)
        if not product:
            raise ValueError(f"No Shopify product found with id {self.remote_product.remote_id}")

        # Build payload for the new image
        payload = {
            'product_id': product.id,
            'src':        self.local_instance.media.image_web_url,
            'position':   self.local_instance.sales_channels_sort_order,
            'alt':        getattr(self.local_instance.media.image, 'name', None),
        }

        image = self.api.Image(payload)
        image.save()
        return image

class ShopifyMediaProductThroughUpdateFactory(GetShopifyApiMixin, RemoteMediaProductThroughUpdateFactory):
    """
    Updates position and alt text of an existing Shopify image.
    """
    remote_model_class = ShopifyImageProductAssociation

    def update_remote(self):
        image = self.api.Image.find(self.remote_instance.remote_id)
        if not image:
            raise ValueError(f"No Shopify image found with id {self.remote_instance.remote_id}")

        image.position = self.local_instance.sales_channels_sort_order
        image.alt = getattr(self.local_instance.media.image, 'name', None)
        image.save()
        return image

class ShopifyMediaProductThroughDeleteFactory(GetShopifyApiMixin, RemoteMediaProductThroughDeleteFactory):
    """
    Deletes a Shopify image by its ID.
    """
    remote_model_class = ShopifyImageProductAssociation
    delete_remote_instance = True

    def delete_remote(self):
        try:
            image = self.api.Image.find(self.remote_instance.remote_id)
        except Exception:
            return True

        return image.destroy()

class ShopifyImageDeleteFactory(RemoteImageDeleteFactory):
    """
    Deletes all image associations when the underlying media object is deleted.
    """
    has_remote_media_instance = False
    delete_media_assign_factory = ShopifyMediaProductThroughDeleteFactory
