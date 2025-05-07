from sales_channels.factories import RemoteInstanceCreateFactory, RemoteInstanceUpdateFactory
from ..models import WoocommerceOrder
from orders.models import Order
from ..mixins import GetWoocommerceAPIMixin


class WoocommerceOrderCreateFactory(RemoteInstanceCreateFactory, GetWoocommerceAPIMixin):
    """
    Factory to create Orders in Woocommerce
    """
    local_model_class = Order
    remote_model_class = WoocommerceOrder
    api_package_name = 'order'
    api_method_name = 'create'

    field_mapping = {
        # Map local fields to remote fields
        # 'local_field': 'remote_field',
    }

    default_field_mapping = {
        # Default values for fields
        # 'remote_field': 'default_value',
    }

    def customize_payload(self, payload):
        """
        Customize the API payload before sending
        """
        # Add custom logic here
        return payload

    def serialize_response(self, response):
        """
        Process the API response
        """
        # Add custom processing here
        return response


class WoocommerceOrderUpdateFactory(RemoteInstanceUpdateFactory, GetWoocommerceAPIMixin):
    """
    Factory to update Orders in Woocommerce
    """
    local_model_class = Order
    remote_model_class = WoocommerceOrder
    api_package_name = 'order'
    api_method_name = 'update'

    field_mapping = {
        # Map local fields to remote fields
        # 'local_field': 'remote_field',
    }

    def customize_payload(self, payload):
        """
        Customize the API payload before sending
        """
        # Add custom logic here
        return payload

    def serialize_response(self, response):
        """
        Process the API response
        """
        # Add custom processing here
        return response
