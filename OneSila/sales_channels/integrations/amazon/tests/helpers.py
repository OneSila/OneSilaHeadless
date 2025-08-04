from unittest.mock import patch


class DisableWooCommerceSignalsMixin:
    """Mixin to disable WooCommerce receivers during Amazon tests."""

    WOOCOMMERCE_SIGNALS = [
        "create_remote_product",
        "delete_remote_product",
        "update_remote_product",
        "sync_remote_product",
        "manual_sync_remote_product",
        "create_remote_product_property",
        "update_remote_product_property",
        "delete_remote_product_property",
        "update_remote_price",
        "update_remote_product_content",
        "update_remote_product_eancode",
        "add_remote_product_variation",
        "remove_remote_product_variation",
        "create_remote_image_association",
        "update_remote_image_association",
        "delete_remote_image_association",
        "delete_remote_image",
    ]

    def setUp(self):
        super().setUp()
        from sales_channels import signals as sc_signals

        self._signal_patchers = [
            patch.object(getattr(sc_signals, name), "send", return_value=[])
            for name in self.WOOCOMMERCE_SIGNALS
        ]
        for patcher in self._signal_patchers:
            patcher.start()
        self.addCleanup(self._stop_signal_patchers)

    def _stop_signal_patchers(self):
        for patcher in self._signal_patchers:
            patcher.stop()
