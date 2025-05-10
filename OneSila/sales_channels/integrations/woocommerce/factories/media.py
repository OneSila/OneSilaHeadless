from sales_channels.factories.products.images import RemoteMediaProductThroughCreateFactory, RemoteMediaProductThroughUpdateFactory, \
    RemoteMediaProductThroughDeleteFactory, RemoteImageDeleteFactory
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceMediaThroughProduct

from .mixins import SerialiserMixin
from ..exceptions import DuplicateError

from core.decorators import log_method_calls

from django.conf import settings

import logging
logger = logging.getLogger(__name__)


class WooCommerceMediaProductThroughMixin(SerialiserMixin):
    # We dont need to store images remotely.
    remote_model_class = WoocommerceMediaThroughProduct
    remote_id_map = 'id'
    # Key is the local field, value is the remote field
    field_mapping = {
        'image_web_url': 'src',
    }

    def create_or_update_images(self):
        """
        Creates or updates images in WooCommerce.
        """
        # As we cannot do an image update, we must update all the images in one go via the product update.
        self.image_urls = [image.image_web_url for image in self.remote_product.local_instance.images.all()]
        if settings.DEBUG:
            # We use some fake images for testing. As local images are not available in the test environment.
            # For the test, we must have the same number of images as the source provides dynamically.
            logger.debug(f"Image upload running in local mode: {self.image_urls}")
            import random
            self.image_urls = [f"https://via.placeholder.com/{random.randint(100, 200)}" for _ in range(len(self.image_urls))]

        payload = [{"src": image_url} for image_url in self.image_urls]
        return self.api.update_product(self.remote_product.remote_id, {"images": payload})


@log_method_calls
class WooCommerceMediaProductThroughCreateFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughCreateFactory):

    def preflight_process(self):
        # FIXME: This create_remote_image()should surely not  be called here?
        # The RemoteMediaProductThroughCreateFactory is to create. Why does
        # it care if the remote existst or not. Check out ParentClass
        super().preflight_process()
        self.create_remote_image()
        # Digging further, running create_remote_image() does nothing neither.
        # almost like the preprocess isnt run.

    def create_remote(self):
        # Continueing on the previous comment, let's check if this is called.
        self.create_remote_image()
        # No. Not called either.

    def create_remote_image(self):
        """
        Creates a remote product in WooCommerce.
        """
        raise NotImplementedError("This should be called, but it is not..")
        return self.create_or_update_images()


class WooCommerceMediaProductThroughUpdateFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughUpdateFactory):
    def update_remote(self):
        """
        Creates a remote product in WooCommerce.
        """
        return self.create_or_update_images()


class WooCommerceMediaProductThroughDeleteFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteMediaProductThroughDeleteFactory):
    def delete_remote_image(self):
        """
        Deletes a remote product in WooCommerce.
        """
        return self.create_or_update_images()


class WooCommerceImageDeleteFactory(WooCommerceMediaProductThroughMixin, GetWoocommerceAPIMixin, RemoteImageDeleteFactory):
    def delete_remote(self):
        """
        Deletes a remote product in WooCommerce.
        """
        return self.create_or_update_images()
