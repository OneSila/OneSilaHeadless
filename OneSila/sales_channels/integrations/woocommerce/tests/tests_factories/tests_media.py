
from .mixins import TestCaseWoocommerceMixin
from django.conf import settings

from sales_channels.integrations.woocommerce.tests.helpers import CreateTestProductMixin
from sales_channels.integrations.woocommerce.factories.media import WooCommerceMediaProductThroughCreateFactory
from sales_channels.integrations.woocommerce.factories.products import WooCommerceProductCreateFactory
from media.models import Image, MediaProductThrough
from media.tests.helpers import CreateImageMixin


import logging
logger = logging.getLogger(__name__)


class WooCommerceMediaProductThroughFactoryTestCase(CreateTestProductMixin, CreateImageMixin, TestCaseWoocommerceMixin):
    def setUp(self):
        super().setUp()
        self.product = self.create_test_product(sku="TEST-prod-create-delete",
            name="Test Product",
            assign_to_sales_channel=True)

    def test_create_images_woocommerce(self):
        image = self.create_and_attach_image(self.product, fname='yellow.png')
        local_image_count = MediaProductThrough.objects.filter(product=self.product).count()
        logger.debug(f"Product has {local_image_count} images pre-woocommerce product create")

        product_create_factory = WooCommerceProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        product_create_factory.run()

        image, media_product_through = self.create_and_attach_image(self.product, fname='red.png')
        logger.debug(f"Created image: {image}")
        logger.debug(f"Product has {self.product.mediaproductthrough_set.count()} image_throughs")
        self.assertEqual(self.product.id, product_create_factory.remote_product.local_instance.id)
        self.assertEqual(self.product.mediaproductthrough_set.count(), 2)

        media_create_factory = WooCommerceMediaProductThroughCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=media_product_through,
            remote_product=product_create_factory.remote_product,
        )
        media_create_factory.run()

        self.assertTrue(media_create_factory.payload.get('images') != None)
        self.assertEqual(len(media_create_factory.payload['images']), 2)

        remote_repsonse = self.api.get_product(product_create_factory.remote_product.remote_id)['images']
        logger.debug(f"Remote response: {remote_repsonse}")
        remote_image_count = len(remote_repsonse)
        local_image_count = MediaProductThrough.objects.filter(product=self.product).count()

        self.assertEqual(remote_image_count, local_image_count)
