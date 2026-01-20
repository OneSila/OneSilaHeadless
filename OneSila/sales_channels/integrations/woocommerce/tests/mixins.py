from unittest.mock import patch

from sales_channels import signals as sc_signals
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel


class WooCommerceSalesChannelTestMixin:
    def setUp(self, *, _unused=None):
        super().setUp()
        self._sales_channel_created_patcher = patch.object(
            sc_signals.sales_channel_created,
            "send",
            return_value=[],
        )
        self._sales_channel_created_patcher.start()
        self.addCleanup(self._sales_channel_created_patcher.stop)

        self._connect_patcher = patch.object(
            WoocommerceSalesChannel,
            "connect",
            return_value=None,
        )
        self._connect_patcher.start()
        self.addCleanup(self._connect_patcher.stop)

        self.sales_channel = WoocommerceSalesChannel.objects.create(
            hostname="https://woocommerce.example.com",
            api_key="api-key",
            api_secret="api-secret",
            api_version=WoocommerceSalesChannel.API_VERSION_CHOICES[0][0],
            timeout=10,
            verify_ssl=False,
            active=True,
            multi_tenant_company=self.multi_tenant_company,
        )
