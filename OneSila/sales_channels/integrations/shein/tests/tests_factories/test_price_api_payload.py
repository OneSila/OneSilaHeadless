from unittest.mock import PropertyMock, patch

from core.tests import TestCase
from currencies.models import Currency
from model_bakery import baker
from products.models import Product

from sales_channels.integrations.shein.factories.prices import SheinPriceUpdateFactory
from sales_channels.integrations.shein.models import (
    SheinSalesChannel,
    SheinSalesChannelView,
)
from sales_channels.models import SalesChannelViewAssign
from sales_channels.models.products import RemotePrice, RemoteProduct


class SheinPriceApiPayloadTest(TestCase):
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
        self.remote_product = RemoteProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="SKU-1",
            remote_id="REMOTE-SKU-1",
        )
        self.view = SheinSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="shein-fr",
            is_default=True,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
        )
        self.currency = Currency.objects.create(
            iso_code="EUR",
            name="Euro",
            multi_tenant_company=self.multi_tenant_company,
        )
        from sales_channels.integrations.shein.models import SheinRemoteCurrency

        SheinRemoteCurrency.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.currency,
            remote_code="EUR",
        )

    def test_calls_price_save_api_when_not_value_only(self):
        self.product.get_price_for_sales_channel = lambda *args, **kwargs: (20, 10)

        factory = SheinPriceUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            get_value_only=False,
            skip_checks=True,
        )

        with patch.object(factory, "shein_post", autospec=True) as mock_post:
            mock_post.return_value.json.return_value = {"code": "0"}
            factory.run()

        mock_post.assert_called_once()
        payload = mock_post.call_args[1]["payload"]["productPriceList"][0]
        self.assertEqual(payload["currencyCode"], "EUR")
        self.assertEqual(payload["productCode"], "REMOTE-SKU-1")
        self.assertEqual(payload["site"], "shein-fr")
        self.assertEqual(payload["shopPrice"], 20)
        self.assertEqual(payload["specialPrice"], 10)

        remote_price = RemotePrice.objects.get(remote_product=self.remote_product)
        self.assertEqual(remote_price.price_data["EUR"]["price"], 20)
