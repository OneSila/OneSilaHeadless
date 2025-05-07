from sales_channels.factories import RemoteInstanceCreateFactory, RemoteInstanceUpdateFactory
from ..models import WoocommerceProduct
from products.models import Product
from ..mixins import GetWoocommerceAPIMixin


class WoocommerceProductCreateFactory(RemoteInstanceCreateFactory, GetWoocommerceAPIMixin):
    """
    Factory to create Products in Woocommerce
    """
    local_model_class = Product
    remote_model_class = WoocommerceProduct
    api_package_name = 'product'
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


class WoocommerceProductUpdateFactory(RemoteInstanceUpdateFactory, GetWoocommerceAPIMixin):
    """
    Factory to update Products in Woocommerce
    """
    local_model_class = Product
    remote_model_class = WoocommerceProduct
    api_package_name = 'product'
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
