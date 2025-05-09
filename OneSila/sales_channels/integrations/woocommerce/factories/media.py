from sales_channels.factories.products.images import RemoteMediaProductThroughCreateFactory, RemoteMediaProductThroughUpdateFactory, \
    RemoteMediaProductThroughDeleteFactory, RemoteImageDeleteFactory
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin

from .mixins import SerialiserMixin
from ..exceptions import DuplicateError


class WooCommerceMediaProductThroughMixin(SerialiserMixin):
    # We dont need to store images remotely.
    remote_model_class = None
    remote_id_map = 'id'
    # Key is the local field, value is the remote field
    field_mapping = {
        'image_web_url': 'src',
    }


class WooCommerceMediaProductThroughCreateFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughCreateFactory):
    pass


class WooCommerceMediaProductThroughUpdateFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughUpdateFactory):
    pass


class WooCommerceMediaProductThroughDeleteFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughDeleteFactory):
    pass


class WooCommerceImageDeleteFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteImageDeleteFactory):
    pass
