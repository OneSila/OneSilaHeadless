from core.tests import TestCase
from model_bakery import baker

from products.models import Product
from sales_channels.integrations.shein.models import SheinProduct, SheinSalesChannel, SheinSalesChannelView
from sales_channels.models import SalesChannelViewAssign


class SheinProductModelTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.test",
            remote_id="SC-URL-1",
        )
        self.view = SheinSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="shein-uk",
            name="UK",
            url="https://www.shein.co.uk/",
            is_default=True,
        )

    def test_url_skc_name_prefers_current_remote_product_skc(self) -> None:
        local_product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=local_product,
            remote_sku="SKU-1",
            skc_name="sz260204174020860851073",
            is_variation=False,
        )

        self.assertEqual(remote_product.url_skc_name, "sz260204174020860851073")

    def test_url_skc_name_falls_back_to_first_child_variation_skc(self) -> None:
        parent_local = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
        )
        child_local = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )

        parent_remote = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent_local,
            remote_sku="PARENT-SKU",
            is_variation=False,
        )
        SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=child_local,
            remote_sku="CHILD-SKU",
            remote_parent_product=parent_remote,
            is_variation=True,
            skc_name="child-skc",
        )

        self.assertEqual(parent_remote.url_skc_name, "child-skc")

    def test_url_skc_name_returns_none_without_skc_or_child_variations(self) -> None:
        local_product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=local_product,
            remote_sku="SKU-2",
            is_variation=False,
        )

        self.assertIsNone(remote_product.url_skc_name)

    def test_sales_channel_view_assign_remote_url_uses_pdsearch_path(self) -> None:
        parent_local = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
        )
        child_local = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )

        parent_remote = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent_local,
            remote_sku="PARENT-SKU-URL",
            is_variation=False,
        )
        SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=child_local,
            remote_sku="CHILD-SKU-URL",
            remote_parent_product=parent_remote,
            is_variation=True,
            skc_name="sz260204174020860851073",
        )

        assign = SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=parent_local,
            sales_channel_view=self.view,
            remote_product=parent_remote,
        )

        self.assertEqual(
            assign.remote_url,
            "https://www.shein.co.uk/pdsearch/sz260204174020860851073/",
        )
