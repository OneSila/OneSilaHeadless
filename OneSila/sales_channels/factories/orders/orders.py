from sales_channels.factories.mixins import PullRemoteInstanceMixin
import logging

logger = logging.getLogger(__name__)


class RemoteOrderPullFactory(PullRemoteInstanceMixin):
    """
    Abstract base factory for pulling remote orders, intended to be extended by specific integrations.
    Provides the basic configuration and defines the required interface for integration-specific factories.
    """

    allow_create = True
    allow_update = False
    allow_delete = False

    def get_order_default_fields(self):
        """Retrieve the fields with the values common to create all the orders"""
        return {
            'multi_tenant_company': self.sales_channel.multi_tenant_company,
            'source': self.sales_channel.integration_ptr,
        }

    def create_local_order(self, remote_data):
        """
        Creates a local order instance from the remote data, using the provided local customer.
        Must be implemented by subclasses.

        :param remote_data: Data from the remote system representing an order.
        """
        raise NotImplementedError("Subclasses must implement create_local_order")

    def populate_items(self, local_order, remote_data, remote_instance_mirror):
        """
        Populates the items for a local order from the remote data.
        Must be implemented by subclasses.

        :param local_order: The local order instance to populate items for.
        :param remote_data: Data from the remote system representing order items.
        :param remote_instance_mirror: The RemoteOrder instance
        """
        raise NotImplementedError("Subclasses must implement populate_items")

    def create_local_order_item(self, local_order, item_data):
        """
        Creates a local order item for the given local order using the item data from the remote system.
        Must be implemented by subclasses.

        :param local_order: The local order instance to which the item belongs.
        :param item_data: Data from the remote system representing an order item.
        """
        raise NotImplementedError("Subclasses must implement create_local_order_item")

    def create_remote_order_item(self, local_item, remote_order, item_data):
        """
        Creates a remote order item mirror instance corresponding to the local order item.
        Must be implemented by subclasses.

        :param local_item: The local item instance to which the item belongs.
        :param remote_order: The remote order instance to which the item belongs.
        :param item_data: Data from the remote system representing an order item.
        """
        raise NotImplementedError("Subclasses must implement create_remote_order_item")
