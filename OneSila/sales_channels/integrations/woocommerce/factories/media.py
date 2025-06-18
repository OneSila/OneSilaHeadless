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


class WooCommerceMediaProductThroughMixin(WooCommerceUpdateRemoteProductMixin, WooCommercePayloadMixin, SerialiserMixin):
    # We dont store images remotely.
    # Instead we need up do full product updates on every change
    # to avoid unexpected nullification of random fields.
    remote_model_class = WoocommerceMediaThroughProduct

    def preflight_process(self):
        if not self.local_instance.media.type == Media.IMAGE:
            logger.warning("Local instance is not an image for WooCommerceMediaProductThroughMixin")
            return False

        return super().preflight_process()

    # def customize_payload(self):
    #     logger.debug(f"Customizing payload for {self.local_instance=}")
    #     return self.apply_media_payload()

    # def create_or_update_images(self):
    #     self.set_woocomerce_product_types()
    #     logger.info(f"{self.__class__.__name__} create_or_update_images: {self.remote_product=}, {self.remote_product.__dict__=}")
    #     logger.info(f"{self.__class__.__name__} create_or_update_images: {self.local_instance=}")
    #     logger.info(f"{self.__class__.__name__} create_or_update_images: {self.is_woocommerce_variant_product=}")

    #     if self.is_woocommerce_variant_product:
    #         parent_id = self.remote_product.remote_parent_product.remote_id
    #         variant_id = self.remote_product.remote_id
    #         return self.api.update_product_variation(parent_id, variant_id, **self.payload)
    #     else:
    #         product_id = self.remote_product.remote_id
    #         return self.api.update_product(product_id, **self.payload)


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
