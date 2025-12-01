from unittest.mock import patch

from core.tests import TestCase
from currencies.models import Currency

from sales_channels.integrations.shein.factories.sales_channels.views import (
    SheinSalesChannelViewPullFactory,
)
from sales_channels.integrations.shein.models import SheinRemoteCurrency, SheinSalesChannel


SITE_LIST_RESPONSE = [
    {
        "main_site": "shein",
        "main_site_name": "SHEIN",
        "sub_site_list": [
            {
                "site_name": "SHEIN法国站",
                "site_abbr": "shein-fr",
                "site_status": 1,
                "store_type": 1,
                "currency": "EUR",
                "symbol_left": "",
                "symbol_right": "€",
            },
            {
                "site_name": "SHEIN波兰站",
                "site_abbr": "shein-pl",
                "site_status": 1,
                "store_type": 1,
                "currency": "PLN",
                "symbol_left": "",
                "symbol_right": "zł",
            },
        ],
    }
]


class SheinSiteListCurrencySyncTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.test",
            remote_id="SC-1",
        )
        self.eur = Currency.objects.create(
            iso_code="EUR",
            name="Euro",
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_syncs_remote_currencies_from_site_list(self):
        factory = SheinSalesChannelViewPullFactory(sales_channel=self.sales_channel)

        with patch.object(
            factory,
            "fetch_site_records",
            return_value=SITE_LIST_RESPONSE,
        ):
            factory.fetch_remote_instances()

        eur_remote = SheinRemoteCurrency.objects.get(
            sales_channel=self.sales_channel,
            remote_code="EUR",
        )
        self.assertEqual(eur_remote.local_instance, self.eur)
        self.assertEqual(eur_remote.symbol_right, "€")

        pln_remote = SheinRemoteCurrency.objects.get(
            sales_channel=self.sales_channel,
            remote_code="PLN",
        )
        self.assertIsNone(pln_remote.local_instance)
        self.assertEqual(pln_remote.symbol_right, "zł")
