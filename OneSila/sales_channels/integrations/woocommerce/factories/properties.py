from sales_channels.factories.properties.properties import (
    RemotePropertyCreateFactory,
    RemotePropertyUpdateFactory,
    RemotePropertyDeleteFactory,
)
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceGlobalAttribute
from .mixins import SerialiserMixin
from ..exceptions import DuplicateError


class WooCommerceGloablAttributeMixin(SerialiserMixin):
    remote_model_class = WoocommerceGlobalAttribute
    remote_id_map = 'id'
    # Key is the local field, value is the remote field
    field_mapping = {
        'name': 'name',
        'internal_name': 'slug',
    }
    already_exists_exception = DuplicateError

    def customize_payload(self):
        """
        Customizes the payload for WooCommerce global attributes
        """
        # Woocom only supports select values for global attributes
        self.payload['type'] = "select"
        self.payload['has_archives'] = True
        return self.payload


class WooCommerceGlobalAttributeCreateFactory(WooCommerceGloablAttributeMixin, GetWoocommerceAPIMixin, RemotePropertyCreateFactory):
    enable_fetch_and_update = True
    update_if_not_exists = True
    update_factory_class = "sales_channels.integrations.woocommerce.factories.properties.WooCommerceGlobalAttributeUpdateFactory"

    def create_remote(self):
        """
        Creates a remote property in WooCommerce.
        """
        # Implement WooCommerce-specific attribute creation
        return self.api.create_attribute(**self.payload)

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
        return self.api.update_attribute(self.remote_instance.remote_id, self.payload)


class WooCommerceGlobalAttributeDeleteFactory(WooCommerceGloablAttributeMixin, GetWoocommerceAPIMixin, RemotePropertyDeleteFactory):
    delete_remote_instance = True

    def delete_remote(self):
        """
        Deletes a remote property in WooCommerce.
        """
        # Implement WooCommerce-specific attribute deletion
        return self.api.delete_attribute(self.remote_instance.remote_id)
