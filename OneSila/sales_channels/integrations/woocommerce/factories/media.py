from sales_channels.factories.products.images import RemoteMediaProductThroughCreateFactory, RemoteMediaProductThroughUpdateFactory, \
    RemoteMediaProductThroughDeleteFactory, RemoteImageDeleteFactory
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceMediaThroughProduct

from .mixins import SerialiserMixin
from ..exceptions import DuplicateError


class WooCommerceMediaProductThroughMixin(SerialiserMixin):
    # We dont need to store images remotely.
    remote_model_class = WoocommerceMediaThroughProduct
    remote_id_map = 'id'
    # Key is the local field, value is the remote field
    field_mapping = {
        'image_web_url': 'src',
    }


class WooCommerceMediaProductThroughCreateFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughCreateFactory):
    def create_remote(self):
        """
        Creates a remote product in WooCommerce.
        """
        # Since we cannot do a image update, we need to do a full product update.
        pass


class WooCommerceMediaProductThroughUpdateFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughUpdateFactory):
    def update_remote(self):
        """
        Creates a remote product in WooCommerce.
        """
        return self.api.create_product(**self.payload)


class WooCommerceMediaProductThroughDeleteFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughDeleteFactory):
    def delete_remote(self):
        """
        Deletes a remote product in WooCommerce.
        """
        return self.api.delete_product(**self.payload)


class WooCommerceImageDeleteFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteImageDeleteFactory):
    def delete_remote(self):
        """
        Deletes a remote product in WooCommerce.
        """
        return self.api.delete_product(**self.payload)
