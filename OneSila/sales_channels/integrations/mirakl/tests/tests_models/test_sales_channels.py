from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.mirakl.models import MiraklSalesChannel
from sales_channels.integrations.mirakl.sub_type_constants import DEFAULT_MIRAKL_SUB_TYPE


class MiraklSalesChannelModelTests(TestCase):
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
