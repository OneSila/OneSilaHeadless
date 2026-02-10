from unittest.mock import patch

from core.tests import TestCase
from currencies.models import Currency
from products.models import Product
from sales_channels.factories.task_queue import TaskTarget
from sales_channels.integrations.magento2.factories.task_queue import MagentoProductPriceAddTask
from sales_channels.integrations.magento2.models import MagentoPrice, MagentoProduct, MagentoSalesChannel
from sales_channels.integrations.magento2.models.taxes import MagentoCurrency
from sales_channels.tests.helpers import DisableMagentoAndWooConnectionsMixin
from sales_channels.helpers import build_price_data, compute_price_data_hash


class MagentoPriceGuardTests(DisableMagentoAndWooConnectionsMixin, TestCase):
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
        self.currency = Currency.objects.create(
            iso_code="USD",
            name="US Dollar",
            symbol="$",
            multi_tenant_company=self.multi_tenant_company,
        )
        MagentoCurrency.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.currency,
            remote_code="USD",
            website_code="base",
            is_default=True,
        )

    def _get_target(self, *, remote_product):
        return TaskTarget(
            sales_channel=self.sales_channel,
            remote_product=remote_product,
        )

    def _build_task(self, *, product):
        return MagentoProductPriceAddTask(
            task_func=lambda *args, **kwargs: None,
            product=product,
            number_of_remote_requests=0,
        )

    def test_guard_blocks_configurable_parent(self):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            sku="PRICE-CONFIG",
        )
        remote_product = MagentoProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=product,
        )
        task_runner = self._build_task(product=product)
        result = task_runner.guard(target=self._get_target(remote_product=remote_product))
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "price_configurable_parent")

    def test_guard_blocks_when_price_unchanged(self):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="PRICE-UNCHANGED",
        )
        remote_product = MagentoProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=product,
        )

        with patch.object(
            Product,
            "get_price_for_sales_channel",
            return_value=(10, 8),
        ):
            price_data = build_price_data(product=product, sales_channel=self.sales_channel)
            price_hash = compute_price_data_hash(price_data=price_data)
            MagentoPrice.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_product=remote_product,
                price_data=price_data,
                price_data_hash=price_hash,
            )

            task_runner = self._build_task(product=product)
            result = task_runner.guard(target=self._get_target(remote_product=remote_product))
            self.assertFalse(result.allowed)
            self.assertEqual(result.reason, "price_unchanged")

    def test_guard_allows_when_price_changed_and_updates_remote(self):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="PRICE-CHANGED",
        )
        remote_product = MagentoProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=product,
        )
        remote_price = MagentoPrice.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=remote_product,
            price_data={"USD": {"price": 9.0, "discount_price": 7.0}},
        )

        with patch.object(
            Product,
            "get_price_for_sales_channel",
            return_value=(10, 8),
        ):
            task_runner = self._build_task(product=product)
            result = task_runner.guard(target=self._get_target(remote_product=remote_product))
            self.assertTrue(result.allowed)
            remote_price.refresh_from_db()
            self.assertEqual(remote_price.price_data["USD"]["price"], 10.0)
            self.assertEqual(remote_price.price_data["USD"]["discount_price"], 8.0)

    def test_guard_allows_when_remote_missing(self):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="PRICE-NO-REMOTE",
        )
        remote_product = MagentoProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=product,
        )

        with patch.object(
            Product,
            "get_price_for_sales_channel",
            return_value=(10, 8),
        ):
            task_runner = self._build_task(product=product)
            result = task_runner.guard(target=self._get_target(remote_product=remote_product))
            self.assertTrue(result.allowed)
            self.assertFalse(MagentoPrice.objects.filter(remote_product=remote_product).exists())
