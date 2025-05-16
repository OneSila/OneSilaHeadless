
from .mixins import TestCaseWoocommerceMixin
from django.conf import settings

from sales_channels.integrations.woocommerce.tests.helpers import CreateTestProductMixin
from sales_channels.integrations.woocommerce.factories.media import WooCommerceMediaProductThroughCreateFactory
from sales_channels.integrations.woocommerce.factories.products import WooCommerceProductCreateFactory
from media.models import Image, MediaProductThrough
from media.tests.helpers import CreateImageMixin
import logging
logger = logging.getLogger(__name__)


class WooCommerceMediaProductThroughFactoryTest(CreateTestProductMixin, CreateImageMixin, TestCaseWoocommerceMixin):
    def setUp(self):
        super().setUp()
        self.product = self.create_test_product(sku="TEST-SKU-001-create-delete", name="Test Product")

    def test_create_images(self):
        image = self.create_and_attach_image(self.product, fname='yellow.png')
        local_image_count = MediaProductThrough.objects.filter(product=self.product).count()
        logger.debug(f"Product has {local_image_count} images pre-woocommerce product create")

        product_create_factory = WooCommerceProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        product_create_factory.run()

        image = self.create_and_attach_image(self.product)
        logger.debug(f"Created image: {image}")
        logger.debug(f"Product has {self.product.mediaproductthrough_set.count()} image_throughs")

        image_two = self.create_and_attach_image(self.product, fname='red.png')
        media_create_factory = WooCommerceMediaProductThroughCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=image_two,
            remote_product=product_create_factory.remote_product,
        )
        media_create_factory.run()

        logger.debug(f"Ran media create factory.....")

        remote_image_count = len(self.api.get_product(product_create_factory.remote_product.remote_id)['images'])
        local_image_count = MediaProductThrough.objects.filter(product=self.product).count()

        self.assertEqual(remote_image_count, local_image_count)
