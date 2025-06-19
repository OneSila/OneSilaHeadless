
from .mixins import TestCaseWoocommerceMixin
from django.conf import settings

from sales_channels.integrations.woocommerce.tests.helpers import CreateTestProductMixin
from sales_channels.integrations.woocommerce.factories.media import WooCommerceMediaProductThroughCreateFactory
from sales_channels.integrations.woocommerce.factories.products import WooCommerceProductCreateFactory
from media.models import Image, MediaProductThrough
from media.tests.helpers import CreateImageMixin


import logging

from ...models import WoocommerceProduct

logger = logging.getLogger(__name__)


class WooCommerceMediaProductThroughFactoryTestCase(CreateTestProductMixin, CreateImageMixin, TestCaseWoocommerceMixin):
    def test_create_images_woocommerce(self):
        self.product = self.create_test_product(sku="TEST-prod-create-delete",
            name="Test Product",
            assign_to_sales_channel=True)
        image = self.create_and_attach_image(self.product, fname='yellow.png')
        local_image_count = MediaProductThrough.objects.filter(product=self.product).count()
        logger.debug(f"Product has {local_image_count} images pre-woocommerce product create")

        remote_instance = WoocommerceProduct.objects.get(local_instance=self.product)
        remote_product = self.api.get_product(remote_instance.remote_id)
        self.assertEqual(len(remote_product['images']), 1)

        image, media_product_through = self.create_and_attach_image(self.product, fname='red.png')
        self.assertEqual(self.product.mediaproductthrough_set.count(), 2)

        remote_product = self.api.get_product(remote_instance.remote_id)
        remote_image_count = len(remote_product['images'])
        local_image_count = MediaProductThrough.objects.filter(product=self.product).count()
        self.assertEqual(remote_image_count, local_image_count)
