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
from .mixins import SerialiserMixin, WooCommercePayloadMixin, \
    WoocommerceRemoteValueConversionMixin
from ..exceptions import DuplicateError

import logging
logger = logging.getLogger(__name__)


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


class WooCommerceProductPropertyMixin(WoocommerceRemoteValueConversionMixin):
    remote_model_class = WoocommerceProductProperty
    remote_id_map = 'id'
    remote_property_factory = WooCommerceGlobalAttributeCreateFactory
    remote_property_select_value_factory = WoocommerceGlobalAttributeValueCreateFactory
    enable_fetch_and_update = True
    update_if_not_exists = True
    update_factory_class = "WooCommerceProductPropertyUpdateFactory"

    # field_mapping = {
    #     'name': 'name',
    #     'is_public_information': 'visible',
    # }

    def get_local_product(self):
        return self.local_instance.product


class WooCommerceProductPropertyCreateFactory(WooCommerceProductPropertyMixin, WooCommercePayloadMixin, RemoteProductPropertyCreateFactory, WoocommerceRemoteValueConversionMixin):
    def create_remote(self):
        """To assign a property to a product we need to concider that woocommerce looks at things as follows:
        - Global Attributes need to be created first but are part of the product properties but must include the slug.
        - Local (Custom) Attributes are just supplied.
        """
        # The attributes are not actually assigned on the product.
        # They are part of the product itself.
        self.remote_value = self.get_remote_value()

        # NOTE What is this about?
        if self.get_value_only:
            self.remote_instance.remote_value = str(self.remote_value)
            self.remote_instance.save()
            # if we ony get the value we don't need to return anything.
            return

        self.update_remote_product()


class WooCommerceProductPropertyUpdateFactory(WooCommerceProductPropertyMixin, WooCommercePayloadMixin, RemoteProductPropertyUpdateFactory):
    def update_remote(self):
        # The attributes are not actually updated on the product.
        # They are set as part of the product. However we do need to update things.
        self.update_remote_product()


class WooCommerceProductPropertyDeleteFactory(WooCommerceProductPropertyMixin, WooCommercePayloadMixin, RemoteProductPropertyDeleteFactory):
    def delete_remote(self):
        # The attributes are not actually updated on the product.
        # They are set as part of the product
        self.update_remote_product()
