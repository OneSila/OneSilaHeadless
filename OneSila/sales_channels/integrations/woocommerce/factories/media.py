from sales_channels.factories.products.images import RemoteMediaProductThroughCreateFactory, RemoteMediaProductThroughUpdateFactory, \
    RemoteMediaProductThroughDeleteFactory, RemoteImageDeleteFactory
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceMediaThroughProduct
from media.models import Media
from .mixins import SerialiserMixin

from core.decorators import log_method_calls

from django.conf import settings

import logging
logger = logging.getLogger(__name__)


class WooCommerceMediaMixin(SerialiserMixin):
    """
    This is the class used to populate all of the
    media on the products.

    Woocommerce needs a full media payload for each product.
    """

    def get_image_url(self, media):
        if settings.DEBUG:
            return f"https://via.placeholder.com/{random.randint(100, 200)}"

        return media.image_web_url

    def get_local_product(self):
        return self.remote_product.local_instance

    def apply_media_payload(self):
        # Woocom requires a full media payload for each product.
        # {
        #     "images": [
        #         {"src": "url"}
        #     ]
        # }
        product = self.get_local_product()
        image_throughs = product.mediaproductthrough_set.filter(media__image_type=Media.IMAGE)

        logger.debug(f"Found {image_throughs.count()} image_throughs for {product=}")

        payload = [{"src": self.get_image_url(i.media)} for i in image_throughs]
        self.payload['images'] = payload

        logger.debug(f"Media payload applied: {self.payload}")
        return self.payload


class WooCommerceMediaProductThroughMixin(WooCommerceMediaMixin, SerialiserMixin):
    # We dont need to store images remotely.
    remote_model_class = WoocommerceMediaThroughProduct
    remote_id_map = 'id'
    # Key is the local field, value is the remote field
    field_mapping = {}

    def preflight_process(self):
        if not self.local_instance.media.is_image():
            return False

        return super().preflight_process()

    def customize_payload(self):
        return self.apply_media_payload()

    def create_or_update_images(self):
        return self.api.update_product(self.remote_product.remote_id, **self.payload)


@log_method_calls
class WooCommerceMediaProductThroughCreateFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughCreateFactory):
    def create_remote(self):
        return self.create_or_update_images()


class WooCommerceMediaProductThroughUpdateFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughUpdateFactory):
    def update_remote(self):
        return self.create_or_update_images()


class WooCommerceMediaProductThroughDeleteFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughDeleteFactory):
    def delete_remote_image(self):
        return self.create_or_update_images()


class WooCommerceImageDeleteFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteImageDeleteFactory):
    def delete_remote(self):
        return self.create_or_update_images()
