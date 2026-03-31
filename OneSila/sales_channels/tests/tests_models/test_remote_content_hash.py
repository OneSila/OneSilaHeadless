from core.tests import TestCase
from products.models import Product
from sales_channels.tests.helpers import DisableMagentoAndWooConnectionsMixin
from sales_channels.integrations.magento2.models import MagentoProduct, MagentoProductContent, MagentoSalesChannel


class RemoteProductContentHashTests(DisableMagentoAndWooConnectionsMixin, TestCase):
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
            sku="CONTENT-HASH",
        )
        self.remote_product = MagentoProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )

    def test_hash_is_set_on_save(self):
        content = MagentoProductContent.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            content_data={"en-gb": {"name": "Hat", "description": "Desc"}},
        )
        self.assertIsNotNone(content.content_data_hash)

    def test_hash_stable_for_language_order(self):
        content = MagentoProductContent.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            content_data={
                "en-gb": {"name": "Hat", "description": "Desc"},
                "fr-fr": {"name": "Chapeau", "description": "Desc FR"},
            },
        )
        initial_hash = content.content_data_hash

        content.content_data = {
            "fr-fr": {"name": "Chapeau", "description": "Desc FR"},
            "en-gb": {"name": "Hat", "description": "Desc"},
        }
        content.save()

        self.assertEqual(content.content_data_hash, initial_hash)

    def test_hash_changes_when_values_change(self):
        content = MagentoProductContent.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            content_data={"en-gb": {"name": "Hat", "description": "Desc"}},
        )
        initial_hash = content.content_data_hash

        content.content_data = {"en-gb": {"name": "Hat", "description": "Updated"}}
        content.save()

        self.assertNotEqual(content.content_data_hash, initial_hash)
