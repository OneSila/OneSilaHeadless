from orders.models import Order
from sales_channels.factories.mixins import PullRemoteInstanceMixin, RemoteInstanceOperationMixin
from sales_channels.models import RemoteLog
from sales_channels.signals import remote_instance_post_update, remote_instance_pre_update
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

    def get_or_create_local_customer(self, remote_data):
        """
        Retrieves or creates a local customer instance from the remote data.
        Must be implemented by subclasses.

        :param remote_data: Data from the remote system representing a customer.
        """
        raise NotImplementedError("Subclasses must implement get_or_create_local_customer")

    def get_or_create_remote_customer(self, local_customer, remote_data, shipping_address, invoice_address):
        """
        Retrieves or creates a remote customer mirror instance from the remote data.
        Must be implemented by subclasses.

        :param local_customer: The local customer instace
        :param remote_data: Data from the remote system representing a customer.
        :param shipping_address: The local shipping address for the order.
        :param invoice_address: The local invoice address for the order.
        """
        raise NotImplementedError("Subclasses must implement get_or_create_remote_customer")

    def create_local_order(self, remote_data, local_customer, shipping_address, invoice_address):
        """
        Creates a local order instance from the remote data, using the provided local customer.
        Must be implemented by subclasses.

        :param remote_data: Data from the remote system representing an order.
        :param local_customer: The local customer instance associated with the order.
        :param shipping_address: The local shipping address for the order.
        :param invoice_address: The local invoice address for the order.
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

    def get_or_create_local_shipping_address(self, remote_data, local_customer):
        """
        Retrieves or creates a local shipping address instance from the remote data.
        Requires the local customer instance.

        :param remote_data: Data from the remote system representing a shipping address.
        :param local_customer: The local customer instance associated with the shipping address.
        """
        raise NotImplementedError("Subclasses must implement get_or_create_local_shipping_address")

    def get_or_create_local_invoice_address(self, remote_data, local_customer):
        """
        Retrieves or creates a local invoice address instance from the remote data.
        Requires the local customer instance.

        :param remote_data: Data from the remote system representing an invoice address.
        :param local_customer: The local customer instance associated with the invoice address.
        """
        raise NotImplementedError("Subclasses must implement get_or_create_local_invoice_address")

    def change_status_after_process(self, remote_data, local_order):
        """
        Changes the status of the local order after processing.
        Must be implemented by subclasses.

        :param local_order: The local order instance whose status needs to be updated.
        """
        raise NotImplementedError("Subclasses must implement change_status_after_process")


class ChangeRemoteOrderStatus(RemoteInstanceOperationMixin):
    """
    Factory to change the status of a remote order based on the local order status.
    Uses RemoteInstanceOperationMixin for shared operations.
    """
    # Define remote status parameters at the class level
    REMOTE_TO_SHIP_STATUS = None  # To be set with the equivalent remote status for 'TO_SHIP'
    REMOTE_SHIPPED_STATUS = None  # To be set with the equivalent remote status for 'SHIPPED'
    REMOTE_CANCELLED_STATUS = None  # To be set with the equivalent remote status for 'CANCELLED'
    REMOTE_HOLD_STATUS = None  # To be set with the equivalent remote status for 'HOLD'

    remote_class= None
    api_package_name = None
    api_method_name = None

    def __init__(self, sales_channel, local_instance, api=None):
        self.sales_channel = sales_channel
        self.api = api if api is not None else self.get_api()
        self.payload = {}
        self.remote_instance = None
        self.remote_status = None
        self.local_instance = local_instance

        self.STATUS_MAPPING = {
            Order.TO_SHIP: self.REMOTE_TO_SHIP_STATUS,
            Order.SHIPPED: self.REMOTE_SHIPPED_STATUS,
            Order.CANCELLED: self.REMOTE_CANCELLED_STATUS,
            Order.HOLD: self.REMOTE_HOLD_STATUS,
        }

    def run(self):
        # Check if the local order status is mapped
        local_status = self.local_instance.status
        if local_status not in self.STATUS_MAPPING:
            logger.debug(f"Status '{local_status}' not mapped for remote update, skipping.")
            return

        # Set the mapped remote status
        self.remote_status = self.STATUS_MAPPING[local_status]

        # Get the remote instance
        self.remote_instance = self.get_remote_instance()
        if not self.remote_instance:
            logger.debug("Remote instance not found, skipping status update.")
            return

        # Build the payload and update the remote instance
        self.build_payload()
        self.update()

    def get_remote_instance(self):
        return self.remote_class.objects.filter(
            local_instance=self.local_instance,
            sales_channel=self.sales_channel
        ).first()

    def build_payload(self):
        # Construct the payload for updating the remote order status
        self.payload = {
            'id': self.remote_instance.remote_id,
            'status': self.remote_status,
        }
        logger.debug(f"Built payload for status update: {self.payload}")

    def update_remote(self):
        # Fetch the API package and method
        api_package = getattr(self.api, self.api_package_name, None)
        if not api_package:
            raise ValueError(f"API package '{self.api_package_name}' not found in the API client.")

        api_method = getattr(api_package, self.api_method_name, None)
        if not api_method:
            raise ValueError(f"API method '{self.api_method_name}' not found in the API package '{self.api_package_name}'.")

        # Execute the API call
        return api_method(**self.customize_payload())

    def update(self):
        log_identifier = self.get_identifier()

        # Send pre-update signal
        remote_instance_pre_update.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

        try:
            logger.debug(f"Updating remote instance with payload: {self.payload}")

            # Attempt to update the remote instance
            response = self.update_remote()
            response_data = self.serialize_response(response)

            # Log the successful update
            self.log_action_for_instance(self.remote_instance, RemoteLog.ACTION_UPDATE, response_data, self.payload, log_identifier)

            # Send post-update signal
            remote_instance_post_update.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

            self.post_update_process()

        except Exception as e:
            self.log_error(e, RemoteLog.ACTION_UPDATE, log_identifier, self.payload)
            raise

    def post_update_process(self):
        pass


class SyncCancelledOrdersFactory(RemoteInstanceOperationMixin):
    """
    Factory to sync canceled orders from the remote system to the local system.
    """
    remote_model_class = None
    api_package_name = 'orders'
    api_method_name = 'fetch_cancelled_orders'

    def __init__(self, sales_channel, api=None):
        self.sales_channel = sales_channel
        self.api = api if api else self.get_api()
        self.remote_instances = []


    def build_payload(self):
        """
        Constructs the payload for fetching canceled orders.
        """
        self.payload = {}
        return self.payload

    def fetch_remote_instances(self):
        """
        Fetch canceled remote orders from the API.
        """
        api_package = getattr(self.api, self.api_package_name)
        api_method = getattr(api_package, self.api_method_name)
        response = api_method(**self.payload)
        self.remote_instances = self.serialize_response(response)

    def get_remote_identifier(self, remote_data):
        """
        Retrieves the unique identifier for the remote instance.
        Override this in subclasses if the identifier retrieval differs.
        """
        return remote_data.get('id')

    def get_remote_instance_mirror(self, remote_data):
        """
        Retrieve the remote mirror model using the identifier and sales channel.
        """
        remote_id = self.get_remote_identifier(remote_data)
        return self.remote_model_class.objects.filter(
            remote_id=remote_id,
            sales_channel=self.sales_channel
        ).first()

    def process_remote_instance(self, remote_data):
        """
        Processes each canceled remote order.
        """
        remote_instance_mirror = self.get_remote_instance_mirror(remote_data)
        if not remote_instance_mirror:
            return

        local_order = remote_instance_mirror.local_instance
        if local_order and local_order.status != Order.CANCELLED:
            local_order.status = Order.CANCELLED
            local_order.save()
            logger.info(f"Updated local order {local_order.reference} to CANCELLED.")

    def process_remote_instances(self):
        """
        Processes all fetched remote instances.
        """
        for remote_data in self.remote_instances:
            self.process_remote_instance(remote_data)

    def run(self):
        """
        Orchestrates the sync process for canceled orders.
        """
        self.build_payload()
        self.fetch_remote_instances()
        self.process_remote_instances()
