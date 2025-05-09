from sales_channels.factories.properties.properties import (
    RemotePropertyCreateFactory,
    RemotePropertyUpdateFactory,
    RemotePropertyDeleteFactory,
    RemotePropertySelectValueCreateFactory,
    RemotePropertySelectValueUpdateFactory,
    RemotePropertySelectValueDeleteFactory,
)


from sales_channels.factories.properties.properties import (
    RemoteProductPropertyCreateFactory,
    RemoteProductPropertyUpdateFactory,
    RemoteProductPropertyDeleteFactory,
)
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceProductProperty, \
    WoocommerceGlobalAttribute, WoocommerceGlobalAttributeValue
from .mixins import SerialiserMixin
from ..exceptions import DuplicateError
from sales_channels.integrations.woocommerce.constants import API_ATTRIBUTE_PREFIX


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
        # Woocom only supports select values for attributes
        # they are multi-select by default and to be treated
        # as such.
        self.payload['type'] = "select"
        self.payload['has_archives'] = True
        return self.payload


class WooCommerceGlobalAttributeCreateFactory(WooCommerceGloablAttributeMixin, GetWoocommerceAPIMixin, RemotePropertyCreateFactory):
    enable_fetch_and_update = True
    update_if_not_exists = True
    # update_factory_class = "sales_channels.integrations.woocommerce.factories.properties.WooCommerceGlobalAttributeUpdateFactory"
    update_factory_class = "WooCommerceGlobalAttributeUpdateFactory"

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

    def preflight_check(self):
        """Ensure we only allow creation of the attribute is 1) public and 2) used for filters"""
        return self.local_instance.is_public_information and self.local_instance.add_to_filters


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


class WoocommerceGlobalAttributeValueMixin(SerialiserMixin):
    remote_model_class = WoocommerceGlobalAttributeValue
    remote_id_map = 'id'
    # Key is the local field, value is the remote field
    field_mapping = {
        'value': 'name',
    }
    already_exists_exception = DuplicateError

    def customize_payload(self):
        """
        Customizes the payload for WooCommerce global attributes
        """
        return self.payload


class WoocommerceGlobalAttributeValueCreateFactory(WoocommerceGlobalAttributeValueMixin, GetWoocommerceAPIMixin, RemotePropertySelectValueCreateFactory):
    update_factory_class = "WoocommerceGlobalAttributeValueUpdateFactory"
    remote_property_factory = WooCommerceGlobalAttributeCreateFactory

    def create_remote(self):
        return self.api.create_attribute_term(
            self.remote_instance.remote_property.remote_id, **self.payload)


class WoocommerceGlobalAttributeValueUpdateFactory(WoocommerceGlobalAttributeValueMixin, GetWoocommerceAPIMixin, RemotePropertySelectValueUpdateFactory):
    create_factory_class = WoocommerceGlobalAttributeValueCreateFactory
    remote_property_factory = WooCommerceGlobalAttributeCreateFactory

    def update_remote(self):
        """
        Updates a remote property in WooCommerce.
        """
        return self.api.update_attribute_value(
            self.remote_instance.remote_property.remote_id, self.remote_instance.remote_id, **self.payload)


class WoocommerceGlobalAttributeValueDeleteFactory(WoocommerceGlobalAttributeValueMixin, GetWoocommerceAPIMixin, RemotePropertySelectValueDeleteFactory):
    delete_remote_instance = True

    def delete_remote(self):
        """
        Deletes a remote property in WooCommerce.
        """
        return self.api.delete_attribute_term(self.remote_instance.remote_property.remote_id, self.remote_instance.remote_id)


class WooCommerceProductPropertyMixin(SerialiserMixin):
    remote_model_class = WoocommerceProductProperty
    remote_id_map = 'id'
    # FIXME: remote_property_factory and remote_property_select_value_factory should be
    # renamed to as remote_property_create_factory and remote_property_select_value_create_factory
    remote_property_factory = WooCommerceGlobalAttributeCreateFactory
    remote_property_select_value_factory = WoocommerceGlobalAttributeValueCreateFactory
    enable_fetch_and_update = True
    update_if_not_exists = True
    update_factory_class = "WooCommerceProductPropertyUpdateFactory"

    field_mapping = {
        'name': 'name',
        'is_public_information': 'visible',
    }

    def slugified_internal_name(self):
        return f"{API_ATTRIBUTE_PREFIX}{self.local_instance.property.internal_name}"

    def customize_payload(self):
        # Woocom only supports select values for attributes
        # they are multi-select by default and to be treated
        # as such.

        # Woocommerce expects this kind of payload as part of the product attributes.
        # {
        #     "attributes": [
        #         {
        #         "id": 1,
        #         "name": "Color",
        #         "slug": "pa_color",  <- This makes it use Global Attribute. Skip if not a global attribute.
        #         "visible": true,
        #         "variation": false, <- This is for variation versions. Sounds like a configurator of sorts.
        #         "options": ["Red", "Blue"]
        #         }
        #     ]
        # }

        # if add_to_filters we include the slug from the global attribute
        payload_addition = {
            "name": self.local_instance.property.name,
            "variation": False,
            "options": [self.local_instance.get_value()]
        }

        if self.local_instance.add_to_filters:
            payload_addition['slug'] = self.slugified_internal_name()

        self.payload.extend(payload_addition)
        return self.payload


class WooCommerceProductPropertyCreateFactory(WooCommerceProductPropertyMixin, GetWoocommerceAPIMixin, RemoteProductPropertyCreateFactory):
    def create_remote(self):
        """To assign a property to a product we need to concider that woocommerce looks at things as follows:
        - Global Attributes need to be created first but are part of the product properties but must include the slug.
        - Local (Custom) Attributes are just supplied.
        """
        # The attributes are not actually assigned on the product.
        # They are part of the product create.
        pass


class WooCommerceProductPropertyUpdateFactory(WooCommerceProductPropertyMixin, GetWoocommerceAPIMixin, RemoteProductPropertyUpdateFactory):
    def update_remote(self):
        # The attributes are not actually updated on the product.
        # They are set as part of the product
        pass


class WooCommerceProductPropertyDeleteFactory(WooCommerceProductPropertyMixin, GetWoocommerceAPIMixin, RemoteProductPropertyDeleteFactory):
    def delete_remote(self):
        # The attributes are not actually updated on the product.
        # They are set as part of the product
        pass
