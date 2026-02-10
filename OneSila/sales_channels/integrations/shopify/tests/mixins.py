from unittest.mock import patch

from sales_channels import signals as sc_signals
from sales_channels.integrations.shopify.models.sales_channels import ShopifySalesChannel


class ShopifySalesChannelTestMixin:
    def setUp(self, *, _unused=None):
        super().setUp()
        self._sales_channel_created_patcher = patch.object(
            sc_signals.sales_channel_created,
            "send",
            return_value=[],
        )
        self._sales_channel_created_patcher.start()
        self.addCleanup(self._sales_channel_created_patcher.stop)

        self.sales_channel = ShopifySalesChannel.objects.create(
            hostname="https://shopify.example.com",
            active=True,
            verify_ssl=False,
            multi_tenant_company=self.multi_tenant_company,
        )
