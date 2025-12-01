from core.tests import TestCase
from model_bakery import baker

from products.models import Product
from sales_channels.integrations.shein.factories.products import SheinSalesChannelAssignFactoryMixin
from sales_channels.integrations.shein.models import SheinSalesChannel, SheinSalesChannelView
from sales_channels.models import SalesChannelViewAssign
from sales_channels.models.products import RemoteProduct


class DummyAssignFactory(SheinSalesChannelAssignFactoryMixin):
    def __init__(self, *, sales_channel):
        self.sales_channel = sales_channel


class SheinSalesChannelAssignMixinTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.test",
            remote_id="SC-1",
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
        )

    def test_builds_site_list_with_default_and_subsites(self):
        default_view = SheinSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="shein",
            is_default=True,
        )
        sub_view = SheinSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="shein-fr",
            is_default=False,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=default_view,
            remote_product=self.remote_product,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=sub_view,
            remote_product=self.remote_product,
        )

        fac = DummyAssignFactory(sales_channel=self.sales_channel)
        site_list = fac.build_site_list(product=self.product)

        self.assertEqual(len(site_list), 1)
        self.assertEqual(site_list[0]["main_site"], "shein")
        self.assertEqual(site_list[0]["sub_site_list"], ["shein-fr"])

    def test_defaults_to_first_assign_when_no_flag(self):
        view = SheinSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="shein",
            is_default=False,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=view,
            remote_product=self.remote_product,
        )

        fac = DummyAssignFactory(sales_channel=self.sales_channel)
        site_list = fac.build_site_list(product=self.product)

        self.assertEqual(site_list[0]["main_site"], "shein")
        self.assertEqual(site_list[0]["sub_site_list"], [])
