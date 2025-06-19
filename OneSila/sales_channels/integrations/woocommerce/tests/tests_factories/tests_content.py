from .tests_products import WooCommerceProductFactoryTestMixin

from sales_channels.integrations.woocommerce.factories.products import (
    WooCommerceProductCreateFactory,
)
from sales_channels.integrations.woocommerce.exceptions import FailedToGetProductBySkuError
from sales_channels.integrations.woocommerce.factories.content import WoocommerceProductContentUpdateFactory


import logging

from ...models import WoocommerceProduct

logger = logging.getLogger(__name__)


class WooCommerceContentUpdateFactoryTest(WooCommerceProductFactoryTestMixin):
    def test_woocommerce_content_update(self):
        sku = 'test_content_update'
        try:
            self.api.delete_product_by_sku(sku)
        except FailedToGetProductBySkuError:
            pass

        product = self.create_test_product(
            sku=sku,
            name="Test Content Update Product",
            assign_to_sales_channel=True,
        )

        translation = product.translations.get(
            language=self.multi_tenant_company.language
        )

        remote_instance = WoocommerceProduct.objects.get(local_instance=product)
        resp_product = self.api.get_product_by_sku(product.sku)
        self.assertEqual(resp_product['name'], translation.name)
        self.assertEqual(resp_product['description'].strip(), translation.description.strip())
        self.assertEqual(resp_product['short_description'].strip(), translation.short_description.strip())

        translation.name = "Test Content Update name update"
        translation.description = "<p>Test Content Update description update</p>"
        translation.short_description = "<p>Test Content Update short description update</p>"
        translation.save()

        factory = WoocommerceProductContentUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_product=remote_instance,
            remote_instance=remote_instance,
            skip_checks=True
        )
        factory.run()

        resp_product = self.api.get_product_by_sku(product.sku)
        self.assertEqual(resp_product['name'], translation.name)
        self.assertEqual(resp_product['description'].strip(), translation.description.strip())
        self.assertEqual(resp_product['short_description'].strip(), translation.short_description.strip())
