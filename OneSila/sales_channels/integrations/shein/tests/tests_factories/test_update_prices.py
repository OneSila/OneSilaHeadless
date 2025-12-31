from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker

from products.models import ConfigurableVariation, Product
from sales_channels.integrations.shein.factories.products import SheinProductUpdateFactory
from sales_channels.integrations.shein.models import (
    SheinProduct,
    SheinSalesChannel,
    SheinSalesChannelView,
)
from sales_channels.models import SalesChannelViewAssign


class SheinProductUpdatePriceHookTest(TestCase):
    def setUp(self):
        super().setUp()
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
            remote_id="SPU-1",
            remote_sku="SKU-1",
            spu_name="SPU-1",
            sku_code="SKU-CODE-1",
        )
        self.view = SheinSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="shein-us",
            is_default=True,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
        )

    @patch("sales_channels.integrations.shein.factories.products.products.SheinPriceUpdateFactory")
    def test_update_calls_price_factory(self, price_factory_cls):
        factory = SheinProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
        )

        factory._update_prices()

        price_factory_cls.assert_called_once()
        _, kwargs = price_factory_cls.call_args
        self.assertTrue(kwargs.get("use_remote_prices"))
        price_factory_cls.return_value.run.assert_called_once()

    @patch("sales_channels.integrations.shein.factories.products.products.SheinPriceUpdateFactory")
    def test_update_calls_price_factory_for_configurable_variations(self, price_factory_cls):
        parent = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            sku="PARENT-1",
        )
        variation = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="VAR-1",
        )
        ConfigurableVariation.objects.create(parent=parent, variation=variation, multi_tenant_company=self.multi_tenant_company)

        remote_parent = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_id="SPU-2",
            remote_sku="PARENT-1",
            spu_name="SPU-2",
        )
        remote_variation = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=variation,
            remote_parent_product=remote_parent,
            is_variation=True,
            remote_id="SKU-REMOTE-1",
            remote_sku="VAR-1",
            sku_code="SKU-CODE-2",
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=parent,
            sales_channel_view=self.view,
            remote_product=remote_parent,
        )

        factory = SheinProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_instance=remote_parent,
        )

        factory._update_prices()

        price_factory_cls.assert_called_once()
        _, kwargs = price_factory_cls.call_args
        self.assertEqual(kwargs.get("local_instance"), variation)
        self.assertEqual(kwargs.get("remote_product"), remote_variation)
        self.assertTrue(kwargs.get("use_remote_prices"))
