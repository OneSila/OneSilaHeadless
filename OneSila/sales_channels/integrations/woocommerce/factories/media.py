from sales_channels.factories.products.images import RemoteMediaProductThroughCreateFactory, RemoteMediaProductThroughUpdateFactory, \
    RemoteMediaProductThroughDeleteFactory, RemoteImageDeleteFactory
from .mixins import WoocommerceProductTypeMixin, GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceMediaThroughProduct
from media.models import Media
from .mixins import SerialiserMixin

from core.decorators import log_method_calls

from django.conf import settings

import logging
logger = logging.getLogger(__name__)


class WooCommerceMediaMixin(WoocommerceProductTypeMixin):
    """
    This is the class used to populate all of the
    media on the products.

    Woocommerce needs a full media payload for each product.
    """

    def get_image_url(self, media):
        import random
        import sys

        # Check if we're running in a test environment
        is_test = settings.TESTING

        logger.debug(f"Checking if in test environment: {is_test}")
        if is_test:
            fname = media.image_web.name.split('/')[-1]
            img_url = f"https://www.onesila.com/testing/{fname}"
            logger.debug(f"Replacing url to {img_url=} due to testing environment")
            return img_url

        return media.image_web_url

    def get_local_product(self):
        return self.remote_product.local_instance

    def get_sku(self):
        """Sets the SKU for the product or variation in the payload."""
        if self.is_woocommerce_variant_product:
            sku = f"{self.parent_local_instance.sku}-{self.local_instance.sku}"
        else:
            product = self.get_local_product()
            sku = product.sku

        return sku

    def apply_media_payload(self):
        # Woocom requires a full media payload for each product.
        # {
        #     "images": [
        #         {"src": "url"}
        #     ]
        # }
        product = self.get_local_product()
        # It seems that omitting the sku from the payload when
        # only images are updated can remove the sku from the product.
        # enforce the sku to ensure it is here at all times.
        self.payload['sku'] = self.get_sku()

        image_throughs = product.mediaproductthrough_set.filter(media__type=Media.IMAGE)
        logger.debug(f"apply_media_payload Found {image_throughs.count()} image_throughs for {product=}")

        payload = [{"src": self.get_image_url(i.media)} for i in image_throughs]
        self.payload['images'] = payload

        logger.debug(f"Media payload applied: {self.payload}")
        return self.payload


class WooCommerceMediaProductThroughMixin(WooCommerceMediaMixin, SerialiserMixin):
    # We dont need to store images remotely.
    remote_model_class = WoocommerceMediaThroughProduct
    remote_id_map = 'id'
    # Key is the local field, value is the remote field
    field_mapping = {
        'sku': 'sku',
        # The price fields are not really fields
        # but "magic" and get set during the payload build.
        'price': 'regular_price',
        'discount': 'sale_price',
        'name': 'name',
        'description': 'description',
        'short_description': 'short_description',
    }

    def preflight_process(self):
        if not self.local_instance.media.type == Media.IMAGE:
            logger.warning("Local instance is not an image for WooCommerceMediaProductThroughMixin")
            return False

        return super().preflight_process()

    def customize_payload(self):
        logger.debug(f"Customizing payload for {self.local_instance=}")
        return self.apply_media_payload()

    def create_or_update_images(self):
        return self.api.update_product(self.remote_product.remote_id, **self.payload)


class WooCommerceMediaProductThroughCreateFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughCreateFactory):
    def create_remote(self):
        return self.create_or_update_images()

    def create_remote_image(self):
        return self.create_or_update_images()

    def customize_remote_instance_data(self):
        self.remote_instance_data['remote_product'] = self.remote_product
        return self.remote_instance_data


class WooCommerceMediaProductThroughUpdateFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughUpdateFactory):
    def update_remote(self):
        return self.create_or_update_images()

    def update_remote_image(self):
        return self.create_or_update_images()


class WooCommerceMediaProductThroughDeleteFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughDeleteFactory):
    def delete_remote(self):
        return self.create_or_update_images()

    def delete_remote_image(self):
        return self.create_or_update_images()


class WooCommerceImageDeleteFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteImageDeleteFactory):
    def delete_remote(self):
        return self.create_or_update_images()
