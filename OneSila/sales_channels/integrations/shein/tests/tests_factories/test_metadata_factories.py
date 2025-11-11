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
