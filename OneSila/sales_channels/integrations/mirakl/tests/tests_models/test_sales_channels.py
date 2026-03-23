from model_bakery import baker

from core.tests import TestCase
from products.models import ConfigurableVariation
from sales_channels.integrations.mirakl.models import MiraklSalesChannel, MiraklSalesChannelView
from sales_channels.integrations.mirakl.sub_type_constants import DEFAULT_MIRAKL_SUB_TYPE
from sales_channels.integrations.mirakl.utils.url_helpers import get_mirakl_remote_url
from sales_channels.models import SalesChannelViewAssign
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklSalesChannelModelTests(DisableMiraklConnectionMixin, TestCase):
    def test_save_infers_sub_type_from_hostname_when_default(self):
        sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://debenhamsuk-prod.mirakl.net/",
            sub_type=DEFAULT_MIRAKL_SUB_TYPE,
        )

        self.assertEqual(sales_channel.sub_type, "debenhams")

    def test_save_keeps_default_sub_type_when_hostname_has_no_match(self):
        sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://unknown-operator.mirakl.net/",
            sub_type=DEFAULT_MIRAKL_SUB_TYPE,
        )

        self.assertEqual(sales_channel.sub_type, DEFAULT_MIRAKL_SUB_TYPE)

    def test_save_preserves_explicit_sub_type(self):
        sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://debenhamsuk-prod.mirakl.net/",
            sub_type="boohoo",
        )

        self.assertEqual(sales_channel.sub_type, "boohoo")

    def test_debenhams_remote_url_uses_remote_sku(self):
        sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://debenhamsuk-prod.mirakl.net/",
            sub_type="debenhams",
        )
        product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
            sku="LOCAL-SKU-1",
        )
        remote_product = baker.make(
            "mirakl.MiraklProduct",
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            local_instance=product,
            remote_sku="REMOTE-SKU-1",
        )
        view = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            remote_id="DEFAULT",
            name="Default",
        )
        assign = baker.make(
            SalesChannelViewAssign,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            sales_channel_view=view,
            product=product,
            remote_product=remote_product,
        )

        self.assertEqual(
            get_mirakl_remote_url(assign),
            "https://www.debenhams.com/search?text=REMOTE-SKU-1",
        )

    def test_debenhams_configurable_remote_url_uses_first_variation_remote_sku(self):
        sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://debenhamsuk-prod.mirakl.net/",
            sub_type="debenhams",
        )
        parent_product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="CONFIGURABLE",
            sku="PARENT-SKU-1",
        )
        first_child = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
            sku="A-CHILD",
        )
        second_child = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
            sku="B-CHILD",
        )
        baker.make(
            ConfigurableVariation,
            multi_tenant_company=self.multi_tenant_company,
            parent=parent_product,
            variation=first_child,
        )
        baker.make(
            ConfigurableVariation,
            multi_tenant_company=self.multi_tenant_company,
            parent=parent_product,
            variation=second_child,
        )
        parent_remote = baker.make(
            "mirakl.MiraklProduct",
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            local_instance=parent_product,
            remote_sku="PARENT-REMOTE",
        )
        baker.make(
            "mirakl.MiraklProduct",
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            local_instance=first_child,
            remote_sku="REMOTE-A",
            is_variation=True,
            remote_parent_product=parent_remote,
        )
        baker.make(
            "mirakl.MiraklProduct",
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            local_instance=second_child,
            remote_sku="REMOTE-B",
            is_variation=True,
            remote_parent_product=parent_remote,
        )
        view = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            remote_id="DEFAULT",
            name="Default",
        )
        assign = baker.make(
            SalesChannelViewAssign,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            sales_channel_view=view,
            product=parent_product,
            remote_product=parent_remote,
        )

        self.assertEqual(
            get_mirakl_remote_url(assign),
            "https://www.debenhams.com/search?text=REMOTE-A",
        )
