from unittest.mock import PropertyMock, patch

from core.tests import TestCase
from model_bakery import baker

from currencies.models import Currency
from sales_channels.integrations.shein.factories.prices import SheinPriceUpdateFactory
from sales_channels.integrations.shein.models import (
    SheinProduct,
    SheinRemoteCurrency,
    SheinSalesChannel,
)
from products.models import Product


class SheinPriceUpdateFactoryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.has_errors_patcher = patch(
            "integrations.models.IntegrationObjectMixin.has_errors",
            new_callable=PropertyMock,
            return_value=False,
        )
        self.has_errors_patcher.start()
        self.addCleanup(self.has_errors_patcher.stop)

        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.test",
            remote_id="SC-1",
            sync_prices=True,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="SKU-1",
            sku_code="SKU-CODE-1",
        )
        self.currency = baker.make(
            Currency,
            iso_code="USD",
            multi_tenant_company=self.multi_tenant_company,
        )
        SheinRemoteCurrency.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.currency,
            remote_code="USD",
        )

    def _set_price(self, full: float, discount: float | None):
        self.product.get_price_for_sales_channel = lambda *args, **kwargs: (full, discount)

    def test_builds_price_info_list_with_special_price(self):
        self._set_price(full=20, discount=10)

        factory = SheinPriceUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.run()

        payload = factory.value["price_info_list"]

        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["currency"], "USD")
        self.assertEqual(payload[0]["base_price"], 20)
        self.assertEqual(payload[0]["special_price"], 10)
        self.assertEqual(factory.price_data["USD"]["price"], 20)
        self.assertEqual(factory.price_data["USD"]["discount_price"], 10)

    def test_skips_special_price_when_absent(self):
        self._set_price(full=15, discount=None)

        factory = SheinPriceUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.run()

        payload = factory.value["price_info_list"]

        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["base_price"], 15)
        self.assertNotIn("special_price", payload[0])

    @patch.object(SheinPriceUpdateFactory, "get_product")
    def test_remote_price_match_skips_update(self, get_product):
        SheinProduct.objects.filter(pk=self.remote_product.pk).update(spu_name="SPU-1")
        self.remote_product.refresh_from_db()

        self._set_price(full=20, discount=None)
        get_product.return_value = {
            "skcInfoList": [
                {
                    "skuInfoList": [
                        {
                            "skuCode": "SKU-CODE-1",
                            "priceInfoList": [
                                {"currency": "USD", "basePrice": 20, "specialPrice": 0},
                            ],
                        }
                    ]
                }
            ]
        }

        factory = SheinPriceUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            get_value_only=False,
            skip_checks=True,
            use_remote_prices=True,
        )
        factory.set_to_update_currencies()

        self.assertEqual(factory.to_update_currencies, [])
