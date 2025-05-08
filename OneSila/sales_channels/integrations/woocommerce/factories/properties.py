from sales_channels.factories.properties.properties import (
    RemotePropertyCreateFactory,
    RemotePropertyUpdateFactory,
    RemotePropertyDeleteFactory,
    RemotePropertySelectValueCreateFactory,
    RemotePropertySelectValueUpdateFactory,
    RemotePropertySelectValueDeleteFactory,
    RemoteProductPropertyCreateFactory,
    RemoteProductPropertyUpdateFactory,
    RemoteProductPropertyDeleteFactory
)
from sales_channels.integrations.woocommerce.mixins import GetWooCommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WooCommerceProperty, WooCommercePropertySelectValue, WooCommerceProductProperty


class WooCommercePropertyCreateFactory(GetWooCommerceAPIMixin, RemotePropertyCreateFactory):
    remote_model_class = WooCommerceProperty
    remote_id_map = 'id'
    # Key is the local field, value is the remote field
    field_mapping = {
        'name': 'name',
        'code': 'slug',
        'type': 'type',
        'order_by': 'menu_order',
        # 'has_archives': True
    }

    def get_update_property_factory(self):
        from sales_channels.integrations.woocommerce.factories.properties import WooCommercePropertyUpdateFactory
        return WooCommercePropertyUpdateFactory

    enable_fetch_and_update = True
    update_if_not_exists = True
    update_factory_class = property(get_update_property_factory)

    def customize_payload(self):
        """
        Customizes the payload for WooCommerce API requirements.
        """
        # Add appropriate attributes based on property type
        property_type = self.local_instance.type

        # Handle property type mapping for WooCommerce
        if property_type == 'select':
            self.payload['type'] = 'select'
        else:
            self.payload['type'] = 'text'  # Default type

        self.payload['slug'] = self.local_instance.code

        return self.payload

    def create_remote(self):
        """
        Creates a remote property in WooCommerce.
        """
        # Implement WooCommerce-specific attribute creation
        response = self.api.create_attribute(self.payload)
        return response

    def serialize_response(self, response):
        """
        Process the API response to extract relevant data.
        """
        return response

    def fetch_existing_remote_data(self):
        """
        Attempts to fetch an existing property by name.
        """
        # Implement WooCommerce-specific attribute fetching
        return self.api.get_attribute(self.local_instance.code)


class WooCommercePropertyUpdateFactory(GetWooCommerceAPIMixin, RemotePropertyUpdateFactory):
    remote_model_class = WooCommerceProperty
    create_factory_class = WooCommercePropertyCreateFactory
    field_mapping = {
        'name': 'name'
    }

    def customize_payload(self):
        """
        Customizes the payload for WooCommerce API requirements.
        """
        return self.payload

    def update_remote(self):
        """
        Updates a remote property in WooCommerce.
        """
        # Implement WooCommerce-specific attribute update
        response = self.api.put(f'products/attributes/{self.remote_instance.remote_id}', data=self.payload)
        return response

    def serialize_response(self, response):
        """
        Process the API response to extract relevant data.
        """
        return response


class WooCommercePropertyDeleteFactory(GetWooCommerceAPIMixin, RemotePropertyDeleteFactory):
    remote_model_class = WooCommerceProperty
    delete_remote_instance = True

    def delete_remote(self):
        """
        Deletes a remote property in WooCommerce.
        """
        # Implement WooCommerce-specific attribute deletion
        response = self.api.delete(f'products/attributes/{self.remote_instance.remote_id}', params={'force': True})
        return response

    def serialize_response(self, response):
        """
        Process the API response to extract relevant data.
        """
        return response


class WooCommercePropertySelectValueCreateFactory(GetWooCommerceAPIMixin, RemotePropertySelectValueCreateFactory):
    remote_model_class = WooCommercePropertySelectValue
    remote_property_factory = WooCommercePropertyCreateFactory
    remote_id_map = 'term_id'
    field_mapping = {
        'value': 'name'
    }

    def preflight_check(self):
        """
        Ensure this is a select-type property before proceeding.
        """
        return not self.local_instance.property.is_product_type

    def preflight_process(self):
        """
        Prepare for attribute term creation.
        """
        super().preflight_process()

    def customize_payload(self):
        """
        Customizes the payload for WooCommerce API requirements.
        """
        # Use select value code for slug if available, otherwise fallback to value
        self.payload['slug'] = getattr(self.local_instance, 'code', self.local_instance.value.lower().replace(' ', '-'))
        return self.payload

    def create_remote(self):
        """
        Creates a remote property select value in WooCommerce.
        """
        # Implement WooCommerce-specific attribute term creation
        response = self.api.post(f'products/attributes/{self.remote_property.remote_id}/terms', data=self.payload)
        return response

    def serialize_response(self, response):
        """
        Process the API response to extract relevant data.
        """
        return response

    def fetch_existing_remote_data(self):
        """
        Attempts to fetch an existing property select value.
        """
        # Implement WooCommerce-specific attribute term fetching
        pass


class WooCommercePropertySelectValueUpdateFactory(GetWooCommerceAPIMixin, RemotePropertySelectValueUpdateFactory):
    remote_model_class = WooCommercePropertySelectValue
    create_factory_class = WooCommercePropertySelectValueCreateFactory
    field_mapping = {
        'value': 'name'
    }

    def preflight_check(self):
        """
        Ensure this is a select-type property before proceeding.
        """
        return not self.local_instance.property.is_product_type

    def customize_payload(self):
        """
        Customizes the payload for WooCommerce API requirements.
        """
        return self.payload

    def update_remote(self):
        """
        Updates a remote property select value in WooCommerce.
        """
        # Implement WooCommerce-specific attribute term update
        self.remote_property = self.remote_instance.remote_property.get_real_instance()
        response = self.api.put(
            f'products/attributes/{self.remote_property.remote_id}/terms/{self.remote_instance.remote_id}',
            data=self.payload
        )
        return response

    def serialize_response(self, response):
        """
        Process the API response to extract relevant data.
        """
        return response


class WooCommercePropertySelectValueDeleteFactory(GetWooCommerceAPIMixin, RemotePropertySelectValueDeleteFactory):
    remote_model_class = WooCommercePropertySelectValue

    def delete_remote(self):
        """
        Deletes a remote property select value in WooCommerce.
        """
        # Implement WooCommerce-specific attribute term deletion
        self.remote_property = self.remote_instance.remote_property.get_real_instance()
        response = self.api.delete(
            f'products/attributes/{self.remote_property.remote_id}/terms/{self.remote_instance.remote_id}',
            params={'force': True}
        )
        return response

    def serialize_response(self, response):
        """
        Process the API response to extract relevant data.
        """
        return response


class WooCommerceProductPropertyCreateFactory(GetWooCommerceAPIMixin, RemoteProductPropertyCreateFactory):
    remote_model_class = WooCommerceProductProperty
    remote_property_factory = WooCommercePropertyCreateFactory
    remote_property_select_value_factory = WooCommercePropertySelectValueCreateFactory

    def get_update_product_property_factory(self):
        from sales_channels.integrations.woocommerce.factories.properties import WooCommerceProductPropertyUpdateFactory
        return WooCommerceProductPropertyUpdateFactory

    enable_fetch_and_update = True
    update_if_not_exists = True
    update_factory_class = property(get_update_product_property_factory)

    def get_remote_value(self):
        """
        Get the appropriate remote value based on property type.
        """
        # Implement value retrieval logic
        if self.local_property.type == 'select':
            # Handle select type properties
            select_value = self.local_instance.property_select_value
            if select_value:
                # Get or create the remote select value
                return select_value.value
        else:
            # Handle text/other type properties
            return self.local_instance.value

    def create_remote(self):
        """
        Creates/assigns a property to a product in WooCommerce.
        """
        self.remote_value = self.get_remote_value()
        if self.get_value_only:
            self.remote_instance.remote_value = str(self.remote_value)
            self.remote_instance.save()
            return

        # Implement WooCommerce-specific product attribute assignment
        # This will likely be handled in a product update operation rather than separately

    def serialize_response(self, response):
        """
        Process the API response to extract relevant data.
        """
        return response


class WooCommerceProductPropertyUpdateFactory(GetWooCommerceAPIMixin, RemoteProductPropertyUpdateFactory):
    remote_model_class = WooCommerceProductProperty
    create_factory_class = WooCommerceProductPropertyCreateFactory
    remote_property_factory = WooCommercePropertyCreateFactory
    remote_property_select_value_factory = WooCommercePropertySelectValueCreateFactory

    def get_remote_value(self):
        """
        Get the appropriate remote value based on property type.
        """
        # Implement value retrieval logic similar to the create factory
        if self.local_property.type == 'select':
            # Handle select type properties
            select_value = self.local_instance.property_select_value
            if select_value:
                return select_value.value
        else:
            # Handle text/other type properties
            return self.local_instance.value

    def update_remote(self):
        """
        Updates a product property in WooCommerce.
        """
        # Implement WooCommerce-specific product attribute update
        # This will likely be handled in a product update operation

    def serialize_response(self, response):
        """
        Process the API response to extract relevant data.
        """
        return response


class WooCommerceProductPropertyDeleteFactory(GetWooCommerceAPIMixin, RemoteProductPropertyDeleteFactory):
    remote_model_class = WooCommerceProductProperty
    delete_remote_instance = True

    def delete_remote(self):
        """
        Removes a property from a product in WooCommerce.
        """
        # Implement WooCommerce-specific product attribute removal
        # This will likely be handled in a product update operation
        return True

    def serialize_response(self, response):
        """
        Process the API response to extract relevant data.
        """
        return response
