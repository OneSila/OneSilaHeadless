from sales_channels.factories.properties.properties import (
    RemotePropertyCreateFactory,
    RemotePropertyUpdateFactory,
    RemotePropertyDeleteFactory,
)
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceGlobalAttribute


class WooCommerceGloablAttributeMixin:
    remote_model_class = WoocommerceGlobalAttribute
    remote_id_map = 'id'
    # Key is the local field, value is the remote field
    field_mapping = {
        'name': 'name',
        'internal_name': 'slug',
    }

    def customize_payload(self):
        """
        Customizes the payload for WooCommerce global attributes
        """
        # Woocom only supports select values for global attributes
        self.payload['type'] = "select"
        self.payload['has_archives'] = True
        return self.payload


class WooCommerceGlobalAttributeCreateFactory(WooCommerceGloablAttributeMixin, GetWoocommerceAPIMixin, RemotePropertyCreateFactory):
    def get_update_property_factory(self):
        from sales_channels.integrations.woocommerce.factories.properties import WooCommerceGlobalAttributeUpdateFactory
        return WooCommerceGlobalAttributeUpdateFactory

    enable_fetch_and_update = True
    update_if_not_exists = True
    update_factory_class = property(get_update_property_factory)

    def create_remote(self):
        """
        Creates a remote property in WooCommerce.
        """
        # Implement WooCommerce-specific attribute creation
        response = self.api.create_attribute(**self.payload)
        return response

    def fetch_existing_remote_data(self):
        """
        Attempts to fetch an existing property by name.
        """
        # Implement WooCommerce-specific attribute fetching
        return self.api.get_attribute_by_code(self.local_instance.internal_name)


class WooCommerceGlobalAttributeUpdateFactory(WooCommerceGloablAttributeMixin, GetWoocommerceAPIMixin, RemotePropertyUpdateFactory):
    create_factory_class = WooCommerceGlobalAttributeCreateFactory

    def update_remote(self):
        """
        Updates a remote property in WooCommerce.
        """
        # Implement WooCommerce-specific attribute update
        response = self.api.update_attribute(self.remote_instance.remote_id, self.payload)
        return response


class WooCommerceGlobalAttributeDeleteFactory(GetWoocommerceAPIMixin, RemotePropertyDeleteFactory):
    remote_model_class = WoocommerceGlobalAttribute
    delete_remote_instance = True

    def delete_remote(self):
        """
        Deletes a remote property in WooCommerce.
        """
        # Implement WooCommerce-specific attribute deletion
        response = self.api.delete_attribute(self.remote_instance.remote_id)
        return response
