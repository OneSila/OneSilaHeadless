from unittest.mock import patch

from sales_channels import signals as sc_signals
from sales_channels.integrations.magento2 import factories as magento_factories
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel


class TaskQueueDispatchPatchMixin:
    def setUp(self, *, _unused=None):
        super().setUp()
        self._task_queue_dispatch_patcher = patch(
            "integrations.factories.task_queue.TaskQueueFactory.dispatch_task",
            return_value=None,
        )
        self._task_queue_dispatch_patcher.start()
        self.addCleanup(self._task_queue_dispatch_patcher.stop)


class DisableMagentoAndWooConnectionsMixin:
    def setUp(self, *, _unused=None):
        super().setUp()
        self._sales_channel_created_patcher = patch.object(
            sc_signals.sales_channel_created,
            "send",
            return_value=[],
        )
        self._sales_channel_created_patcher.start()
        self.addCleanup(self._sales_channel_created_patcher.stop)

        self._magento_connect_patcher = patch.object(
            MagentoSalesChannel,
            "connect",
            return_value=None,
        )
        self._magento_connect_patcher.start()
        self.addCleanup(self._magento_connect_patcher.stop)

        self._woo_connect_patcher = patch.object(
            WoocommerceSalesChannel,
            "connect",
            return_value=None,
        )
        self._woo_connect_patcher.start()
        self.addCleanup(self._woo_connect_patcher.stop)

        self._magento_get_api_patcher = patch.object(
            magento_factories.mixins,
            "get_api",
            return_value=None,
        )
        self._magento_get_api_patcher.start()
        self.addCleanup(self._magento_get_api_patcher.stop)
