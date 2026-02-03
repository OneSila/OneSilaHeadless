from core.tests import TestCase

from products.models import Product
from sales_channels.tests.helpers import DisableMagentoAndWooConnectionsMixin
from sales_channels.integrations.magento2.models import MagentoPrice, MagentoProduct, MagentoSalesChannel


class RemotePriceHashTests(DisableMagentoAndWooConnectionsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = MagentoSalesChannel.objects.create(
            hostname="https://magento.example.com",
            host_api_username="api-user",
            host_api_key="api-key",
            authentication_method=MagentoSalesChannel.AUTH_METHOD_CHOICES[0][0],
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="PRICE-HASH",
        )
        self.remote_product = MagentoProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )

    def test_hash_is_set_on_save(self):
        price = MagentoPrice.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            price_data={"EUR": {"price": 10.0, "discount_price": 8.0}},
        )
        self.assertIsNotNone(price.price_data_hash)

    def test_hash_stable_for_currency_order(self):
        price = MagentoPrice.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            price_data={
                "USD": {"price": 12.0, "discount_price": None},
                "EUR": {"price": 10.0, "discount_price": 8.0},
            },
        )
        initial_hash = price.price_data_hash

        price.price_data = {
            "EUR": {"price": 10.0, "discount_price": 8.0},
            "USD": {"price": 12.0, "discount_price": None},
        }
        price.save()

        self.assertEqual(price.price_data_hash, initial_hash)

    def test_hash_changes_when_values_change(self):
        price = MagentoPrice.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            price_data={"EUR": {"price": 10.0, "discount_price": 8.0}},
        )
        initial_hash = price.price_data_hash

        price.price_data = {"EUR": {"price": 11.0, "discount_price": 8.0}}
        price.save()

        self.assertNotEqual(price.price_data_hash, initial_hash)
