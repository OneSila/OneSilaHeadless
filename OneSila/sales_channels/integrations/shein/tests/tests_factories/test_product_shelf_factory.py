from core.tests import TestCase
from model_bakery import baker

from products.models import Product
from sales_channels.integrations.shein.factories.products.shelf import (
    SheinProductShelfUpdateFactory,
)
from sales_channels.integrations.shein.models import SheinProduct, SheinSalesChannel, SheinSalesChannelView
from sales_channels.models import SalesChannelViewAssign
from sales_channels.models.products import RemoteProduct


class SheinProductShelfUpdateFactoryTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.test",
            remote_id="SC-1",
        )
        self.view = SheinSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="shein-uk",
            is_default=True,
        )

    def _assign(self, *, product, remote_product) -> None:
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=product,
            sales_channel_view=self.view,
            remote_product=remote_product,
        )

    def test_build_payload_for_simple_product(self) -> None:
        product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_sku="SKU-1",
            skc_name="SKC-1",
            status=RemoteProduct.STATUS_COMPLETED,
        )
        self._assign(product=product, remote_product=remote_product)

        factory = SheinProductShelfUpdateFactory(
            sales_channel=self.sales_channel,
            remote_product=remote_product,
            shelf_state=1,
        )

        payload = factory.build_payload()

        self.assertEqual(payload["skc_site_info_list"][0]["skc_name"], "SKC-1")
        self.assertEqual(payload["skc_site_info_list"][0]["shelf_state"], 1)
        self.assertEqual(payload["skc_site_info_list"][0]["site_list"], ["shein-uk"])

    def test_build_payload_for_configurable_product(self) -> None:
        parent = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
        )
        remote_parent = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_sku="PARENT",
            status=RemoteProduct.STATUS_COMPLETED,
        )
        self._assign(product=parent, remote_product=remote_parent)

        child_one = baker.make(Product, multi_tenant_company=self.multi_tenant_company, type=Product.SIMPLE)
        child_two = baker.make(Product, multi_tenant_company=self.multi_tenant_company, type=Product.SIMPLE)
        SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=child_one,
            remote_sku="CHILD-1",
            remote_parent_product=remote_parent,
            skc_name="SKC-ONE",
            status=RemoteProduct.STATUS_COMPLETED,
        )
        SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=child_two,
            remote_sku="CHILD-2",
            remote_parent_product=remote_parent,
            skc_name="SKC-TWO",
            status=RemoteProduct.STATUS_COMPLETED,
        )

        factory = SheinProductShelfUpdateFactory(
            sales_channel=self.sales_channel,
            remote_product=remote_parent,
            shelf_state=1,
        )

        payload = factory.build_payload()

        names = {entry["skc_name"] for entry in payload["skc_site_info_list"]}
        self.assertEqual(names, {"SKC-ONE", "SKC-TWO"})
