from sales_channels.factories.products.images import (
    RemoteProductImageCreateFactory,
    RemoteProductImageUpdateFactory,
    RemoteProductImageDeleteFactory,
)
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


class WooCommerceMediaProductThroughCreateFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteProductImageCreateFactory):
    pass


class WooCommerceMediaProductThroughUpdateFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteProductImageUpdateFactory):
    pass


class WooCommerceMediaProductThroughDeleteFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteProductImageDeleteFactory):
    pass
