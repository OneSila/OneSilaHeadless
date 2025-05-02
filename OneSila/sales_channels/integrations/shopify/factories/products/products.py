from sales_channels.factories.products.products import (
    RemoteProductSyncFactory,
    RemoteProductCreateFactory,
    RemoteProductUpdateFactory,
    RemoteProductDeleteFactory,
)
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models.products import ShopifyProduct
from sales_channels.integrations.shopify.factories.products.eancodes import ShopifyEanCodeUpdateFactory
from sales_channels.integrations.shopify.factories.products.images import (
    ShopifyMediaProductThroughCreateFactory,
    ShopifyMediaProductThroughUpdateFactory,
    ShopifyMediaProductThroughDeleteFactory,
)
from sales_channels.integrations.shopify.factories.properties.properties import (
    ShopifyProductPropertyCreateFactory,
    ShopifyProductPropertyUpdateFactory,
    ShopifyProductPropertyDeleteFactory,
)
import logging

logger = logging.getLogger(__name__)


class ShopifyProductSyncFactory(GetShopifyApiMixin, RemoteProductSyncFactory):
    remote_model_class = ShopifyProduct

    # Sub-factories for images, metafields, EAN, etc.
    remote_image_assign_create_factory = ShopifyMediaProductThroughCreateFactory
    remote_image_assign_update_factory = ShopifyMediaProductThroughUpdateFactory
    remote_image_assign_delete_factory = ShopifyMediaProductThroughDeleteFactory

    remote_product_property_create_factory = ShopifyProductPropertyCreateFactory
    remote_product_property_update_factory = ShopifyProductPropertyUpdateFactory
    remote_product_property_delete_factory = ShopifyProductPropertyDeleteFactory

    remote_eancode_update_factory = ShopifyEanCodeUpdateFactory

    # References to create/update/delete product factories
    sync_product_factory   = property(lambda self: ShopifyProductSyncFactory)
    create_product_factory = property(lambda self: ShopifyProductCreateFactory)
    delete_product_factory = property(lambda self: ShopifyProductDeleteFactory)
    add_variation_factory  = property(lambda self: ShopifyProductSyncFactory)

    # Local field → Shopify REST API field mapping
    field_mapping = {
        'name':              'title',          # product.title
        'url_key':           'handle',         # product.handle (URL key)
        'description':       'body_html',      # product.body_html
        'active':            'published',      # product.published (boolean)
        # 'sku' and 'price' are handled via variants sub-factories or through a single-variant payload
    }

    def get_saleschannel_remote_object(self, sku):
        """
        Used by CreateFactory to detect existing remote product by handle/variants.
        Override if needed.
        """
        return self.api.Product.find(handle=sku)


class ShopifyProductCreateFactory(ShopifyProductSyncFactory, RemoteProductCreateFactory):
    api_package_name = 'Product'
    api_method_name = 'create'

    def perform_remote_action(self):
        # Build complete payload structure for new product, including variants
        payload = {'product': self.payload.copy()}
        # TODO: insert initial variant data into payload, e.g. payload['product']['variants'] = [{...}]
        product = self.api.Product.create(payload)
        response_data = product.to_dict()

        # Update mirror
        self.remote_instance.remote_id = product.id
        self.remote_instance.save()

        return product

    def serialize_response(self, response):
        return response.to_dict()


class ShopifyProductUpdateFactory(ShopifyProductSyncFactory, RemoteProductUpdateFactory):
    api_package_name = 'Product'
    api_method_name = 'update'

    def perform_remote_action(self):
        product = self.api.Product.find(self.remote_instance.remote_id)
        if not product:
            raise ValueError(f"No Shopify product found with id {self.remote_instance.remote_id}")

        # Apply top-level updates
        for field, val in self.payload.items():
            setattr(product, field, val)
        product.save()

        return product

    def serialize_response(self, response):
        return response.to_dict()


class ShopifyProductDeleteFactory(GetShopifyApiMixin, RemoteProductDeleteFactory):
    remote_model_class = ShopifyProduct
    delete_remote_instance = True

    def delete_remote(self):
        product = self.api.Product.find(self.remote_instance.remote_id)
        if not product:
            return True
        return product.destroy()
