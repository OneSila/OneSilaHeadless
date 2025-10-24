"""Tests for Shein remote metadata pull factories."""

from unittest.mock import patch

from currencies.models import Currency
from core.tests import TestCase
from model_bakery import baker

from sales_channels.integrations.shein.factories.sales_channels import (
    SheinMarketplacePullFactory,
)
from sales_channels.integrations.shein.models import (
    SheinRemoteCurrency,
    SheinRemoteMarketplace,
    SheinSalesChannel,
    SheinSalesChannelView,
)


SITE_LIST_PAYLOAD = [
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
                "site_name": "SHEIN西班牙站",
                "site_abbr": "shein-es",
                "site_status": 1,
                "store_type": 1,
                "currency": "EUR",
                "symbol_left": "",
                "symbol_right": "€",
            },
        ],
    }
]


class SheinMetadataFactoriesTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            hostname="https://fr.shein.com",
            multi_tenant_company=self.multi_tenant_company,
            open_key_id="open-key",
            secret_key="secret-key",
        )
        patcher = patch(
            "sales_channels.integrations.shein.factories.mixins.SheinSiteListMixin._call_site_list_api",
            return_value=SITE_LIST_PAYLOAD,
        )
        self.mock_site_list = patcher.start()
        self.addCleanup(patcher.stop)

    def test_marketplace_factory_syncs_storefronts(self) -> None:
        baker.make(
            Currency,
            iso_code="EUR",
            multi_tenant_company=self.multi_tenant_company,
        )

        SheinMarketplacePullFactory(sales_channel=self.sales_channel).run()

        marketplaces = SheinRemoteMarketplace.objects.filter(sales_channel=self.sales_channel)
        self.assertEqual(marketplaces.count(), 2)

        default_marketplace = marketplaces.get(remote_id="shein-fr")
        self.assertTrue(default_marketplace.is_default)
        self.assertEqual(default_marketplace.name, "SHEIN法国站")

        secondary_marketplace = marketplaces.get(remote_id="shein-es")
        self.assertFalse(secondary_marketplace.is_default)

        default_view = SheinSalesChannelView.objects.get(
            sales_channel=self.sales_channel,
            remote_id="shein-fr",
        )
        self.assertEqual(default_view.name, "SHEIN法国站")
        self.assertEqual(default_view.url, "https://fr.shein.com")
        self.assertTrue(default_view.is_default)
        self.assertEqual(default_view.marketplace, default_marketplace)

        secondary_view = SheinSalesChannelView.objects.get(
            sales_channel=self.sales_channel,
            remote_id="shein-es",
        )
        self.assertEqual(secondary_view.name, "SHEIN西班牙站")
        self.assertFalse(secondary_view.is_default)
        self.assertEqual(secondary_view.marketplace, secondary_marketplace)

        currencies = SheinRemoteCurrency.objects.filter(sales_channel=self.sales_channel)
        self.assertEqual(currencies.count(), 1)

        remote_currency = currencies.first()
        self.assertEqual(remote_currency.remote_code, "EUR")
        self.assertEqual(remote_currency.remote_id, "EUR")
        self.assertEqual(remote_currency.symbol_right, "€")
        self.assertIsNotNone(remote_currency.local_instance)
        self.assertEqual(remote_currency.local_instance.iso_code, "EUR")
