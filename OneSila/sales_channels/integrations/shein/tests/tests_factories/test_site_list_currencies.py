from unittest.mock import PropertyMock, patch

from core.tests import TestCase
from currencies.models import Currency

from sales_channels.integrations.shein.factories.sales_channels.views import (
    SheinSalesChannelViewPullFactory,
)
from sales_channels.integrations.shein.models import (
    SheinRemoteCurrency,
    SheinSalesChannel,
    SheinSalesChannelView,
)


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
            factory.run()

        fr_view = SheinSalesChannelView.objects.get(sales_channel=self.sales_channel, remote_id="shein-fr")
        pl_view = SheinSalesChannelView.objects.get(sales_channel=self.sales_channel, remote_id="shein-pl")

        eur_remote = SheinRemoteCurrency.objects.get(
            sales_channel=self.sales_channel,
            sales_channel_view=fr_view,
            remote_code="EUR",
        )
        self.assertEqual(eur_remote.local_instance, self.eur)
        self.assertEqual(eur_remote.symbol_right, "€")

        pln_remote = SheinRemoteCurrency.objects.get(
            sales_channel=self.sales_channel,
            sales_channel_view=pl_view,
            remote_code="PLN",
        )
        self.assertIsNone(pln_remote.local_instance)
        self.assertEqual(pln_remote.symbol_right, "zł")

    def test_pull_keeps_existing_view_name(self):
        SheinSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="shein-fr",
            name="Custom FR",
            site_status=0,
        )

        factory = SheinSalesChannelViewPullFactory(sales_channel=self.sales_channel)

        with patch.object(
            factory,
            "fetch_site_records",
            return_value=SITE_LIST_RESPONSE,
        ):
            factory.run()

        fr_view = SheinSalesChannelView.objects.get(sales_channel=self.sales_channel, remote_id="shein-fr")
        self.assertEqual(fr_view.name, "Custom FR")
        self.assertEqual(fr_view.site_status, 1)
