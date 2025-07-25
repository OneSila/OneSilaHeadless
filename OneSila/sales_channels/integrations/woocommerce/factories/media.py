from sales_channels.factories.products.images import RemoteMediaProductThroughCreateFactory, RemoteMediaProductThroughUpdateFactory, \
    RemoteMediaProductThroughDeleteFactory, RemoteImageDeleteFactory
from .mixins import WoocommerceProductTypeMixin, GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceMediaThroughProduct
from media.models import Media
from .mixins import SerialiserMixin, WooCommercePayloadMixin, WooCommerceUpdateRemoteProductMixin

from core.decorators import log_method_calls

from django.conf import settings

import logging
logger = logging.getLogger(__name__)


class WooCommerceMediaProductThroughMixin(WooCommercePayloadMixin, WooCommerceUpdateRemoteProductMixin, SerialiserMixin):
    # We dont store images remotely.
    # Instead we need up do full product updates on every change
    # to avoid unexpected nullification of random fields.
    remote_model_class = WoocommerceMediaThroughProduct

    def preflight_process(self):
        if not self.local_instance.media.type == Media.IMAGE:
            logger.warning("Local instance is not an image for WooCommerceMediaProductThroughMixin")
            return False

        return super().preflight_process()


class WooCommerceMediaProductThroughCreateFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughCreateFactory):
    def create_remote(self):
        return self.update_remote_product()

    def create_remote_image(self):
        return self.update_remote_product()

    def customize_remote_instance_data(self):
        self.remote_instance_data['remote_product'] = self.remote_product
        return self.remote_instance_data


class WooCommerceMediaProductThroughUpdateFactory(WooCommerceMediaProductThroughMixin, RemoteMediaProductThroughUpdateFactory):

    def update_remote(self):
        return self.update_remote_product()

    def update_remote_image(self):
        return self.update_remote_product()


class WooCommerceMediaProductThroughDeleteFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughDeleteFactory):
    def delete_remote(self):
        return self.update_remote_product()

    def delete_remote_image(self):
        return self.update_remote_product()


class WooCommerceImageDeleteFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteImageDeleteFactory):
    def delete_remote(self):
        return self.update_remote_product()
