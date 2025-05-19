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
from properties.models import ProductProperty, Property
from django.db.models import Q, Count
from django.utils.functional import cached_property
from collections.abc import Iterable

import logging
logger = logging.getLogger(__name__)


class WoocommerceRemoteValueConversionMixin:
    """ Convert OneSila payloads to WooCommerce expected format."""

    def get_remote_value(self):
        # Get the local property type and value in the remote format
        property_type = self.local_property.type
        value = self.local_instance.get_value()

        if property_type == Property.TYPES.INT:
            return self.get_int_value(value)
        elif property_type == Property.TYPES.FLOAT:
            return self.get_float_value(value)
        elif property_type == Property.TYPES.BOOLEAN:
            return self.get_boolean_value(value)
        elif property_type == Property.TYPES.SELECT:
            return self.get_select_value(value)
        elif property_type == Property.TYPES.MULTISELECT:
            return self.get_multi_select_value(value)
        elif property_type == Property.TYPES.TEXT:
            return self.get_text_value(value)
        elif property_type == Property.TYPES.DESCRIPTION:
            return self.get_description_value(value)
        elif property_type == Property.TYPES.DATE:
            return self.get_date_value(value)
        elif property_type == Property.TYPES.DATETIME:
            return self.get_datetime_value(value)
        else:
            raise NotImplementedError(f"Property type {property_type} is not supported.")

    def get_int_value(self, value):
        """Handles int value types."""
        return value

    def get_float_value(self, value):
        """Handles float value types."""
        return value

    def get_boolean_value(self, value: bool) -> int:
        """Converts boolean values to 1 (True) or 0 (False) as required by Magento."""
        return value

    def get_select_value(self, value):
        """Handles select and multiselect values."""
        return value

    def get_multi_select_value(self, value):
        """Handles multi-select values."""
        return value

    def get_text_value(self, value):
        """Handles text values."""
        return value

    def get_description_value(self, value):
        """Handles description values."""
        return value

    def get_date_value(self, value):
        """Handles date values."""
        return value

    def get_datetime_value(self, value):
        """Handles datetime values."""
        return value

    # def format_date(self, date_value):
    #     """Formats date values to include time as '00:00:00' in Magento compatible format."""
    #     if date_value:
    #         # Formatting date to include time as 00:00:00
    #         return date_value.strftime('%d-%m-%Y 00:00:00')

    # def format_datetime(self, datetime_value):
    #     """Formats datetime values to Magento compatible string format."""
    #     if datetime_value:
    #         return datetime_value.strftime('%d-%m-%Y %H:%M:%S')


class WooCommerceProductAttributeMixin(SerialiserMixin):
    """
    This is the class used to populate all of the
    attriubtes on the products.

    Woocommerce needs a full Attribute payload for each product.
    Including EANCodes.

    So to be more precies:
    - local attributes = non-filter ones
    - global attributes = filter ones
    - ean-codes
    are all part of the payload always and every time.
    """
    remote_id_map = 'id'
    global_attribute_model_class = WoocommerceGlobalAttribute

    def slugified_internal_name(self, property):
        return f"{API_ATTRIBUTE_PREFIX}{property.internal_name}"

    def get_local_product(self):
        return self.remote_product.local_instance

    def remote_product_is_variation(self):
        try:
            return self.remote_product.is_variation
        except AttributeError:
            return False

    def set_configurator_properties(self):
        product = self.get_local_product()
        product_rule = product.get_product_rule()

        # Get all variations
        variations = product.get_configurable_variations(active_only=True)

        # Get unique property values across variations
        self.configurator_properties = product.get_configurator_properties(product_rule=product_rule)
        self.configurator_property_ids = self.configurator_properties.values_list('id', flat=True)

    def get_configurator_property_values(self, prop):
        """
        Get all unique property values for the configurator properties across all variations.
        Returns a dictionary mapping property IDs to lists of their values.
        """
        if not hasattr(self, 'configurator_properties'):
            self.set_configurator_properties()

        product = self.get_local_product()
        variations = product.get_configurable_variations(active_only=True)

        # Initialize dictionary to store property values
        property_values = set()

        # Collect values from all variations for this property
        for variation in variations:
            # Get the product property for this variation and property
            product_property = ProductProperty.objects.get(
                product=variation,
                property=prop
            )

            # For select properties, get the selected value
            if prop.type == Property.SELECT:
                property_values.add(product_property.get_value())

        logger.debug(f"Collected configurator property values: {property_values}")
        return list(property_values)

    def set_product_properties_to_apply_payload(self):
        product = self.get_local_product()
        self.product_properties = ProductProperty.objects.filter(
            product=product
        )

    def set_filterable_property_ids(self):
        self.filterable_property_ids = self.product_properties.\
            filter(Q(property__add_to_filters=True) | Q(property__is_product_type=True)).\
            distinct().\
            values_list('id', flat=True)

    def set_product_rule(self):
        product = self.get_local_product()
        self.product_rule = product.get_product_rule()

    def apply_attribute_payload(self):
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
        # FIXME: The properties names and values should be loaded dynamically based on the language.
        # currently they are just the default values.

        product = self.get_local_product()
        is_variation = self.remote_product_is_variation()
        ean_code = product.eancode_set.last()
        self.set_product_rule()
        self.set_product_properties_to_apply_payload()
        self.set_filterable_property_ids()

        # What is this product about?  How does it relate and what are the types?
        if product.is_configurable():
            is_woocommerce_simple_product = False
            is_woocommerce_configurable_product = True
            is_woocommerce_variant_product = False
        elif product.is_simple():
            if is_variation:
                is_woocommerce_simple_product = True
                is_woocommerce_configurable_product = False
                is_woocommerce_variant_product = False
            else:
                is_woocommerce_simple_product = False
                is_woocommerce_configurable_product = False
                is_woocommerce_variant_product = True
        else:
            raise ValueError(f"Product {product} is not configurable or simple. Configure other types.")

        attribute_payload = []

        # There are 3 distinct ways of adding attributes on the payload it seems.
        # So let's just run through the cases and apply the correct format.
        if is_woocommerce_simple_product or is_woocommerce_configurable_product:
            # Variable (configurable) or Simple (non-configurable) products
            # use plurar form.
            if ean_code:
                attribute_payload.append({
                    'name': 'EAN Code',
                    'visible': True,
                    'variation': False,
                    'options': [ean_code.ean_code]
                })

            # Now we want to add all of the properties.
            # if they are a product-type or a filterable property they will
            # already exists as a global attributes.
            # else - a custom one.
            for prop in self.product_properties.iterator():
                try:
                    ga = self.global_attribute_model_class.objects.get(local_instance=prop.property)
                    value = prop.get_serialised_value()

                    # WooCommerce expects a list of values for all global attributes.
                    if not isinstance(value, Iterable):
                        value = [value]

                    attribute_payload.append({
                        'id': ga.remote_id,
                        'name': prop.property.name,
                        'options': value
                    })
                except self.global_attribute_model_class.DoesNotExist:
                    attribute_payload.append({
                        'name': prop.property.name,
                        'options': [prop.get_serialised_value()]
                    })

                if is_woocommerce_configurable_product:
                    for prop in self.configurator_properties.iterator():
                        ga = self.global_attribute_model_class.objects.get(local_instance=prop)
                        values = self.get_configurator_property_values(prop)
                        attribute_payload.append({
                            "id": ga.remote_id,
                            "options": values,
                        })
        elif is_woocommerce_variant_product:
            # Simple Variations (variation) use a singular form.
            if ean_code:
                attribute_payload.append({
                    'name': 'EAN Code',
                    'visible': True,
                    'option': [ean_code.ean_code]
                })

            for prop in self.product_properties.iterator():
                try:
                    ga = self.global_attribute_model_class.objects.get(local_instance=prop.property)
                    attribute_payload.append({
                        'id': ga.remote_id,
                        'option': prop.get_serialised_value(),
                    })
                except self.global_attribute_model_class.DoesNotExist:
                    # FIXME: This does not support mulit-values.
                    attribute_payload.append({
                        'name': prop.property.name,
                        'visible': True,
                        'option': prop.get_serialised_value()
                    })

        self.payload['attributes'] = attribute_payload
        logger.debug(f"Attribute payload applied: {self.payload}")
        return self.payload


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
        allowed_type = self.local_instance.is_product_type or self.local_instance.add_to_filters
        is_public = self.local_instance.is_public_information
        return allowed_type and is_public


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


class WooCommerceProductPropertyMixin(WooCommerceProductAttributeMixin, SerialiserMixin, WoocommerceRemoteValueConversionMixin):
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


class WooCommerceProductPropertyCreateFactory(WooCommerceProductPropertyMixin, GetWoocommerceAPIMixin, RemoteProductPropertyCreateFactory, WoocommerceRemoteValueConversionMixin):
    def create_remote(self):
        """To assign a property to a product we need to concider that woocommerce looks at things as follows:
        - Global Attributes need to be created first but are part of the product properties but must include the slug.
        - Local (Custom) Attributes are just supplied.
        """
        # The attributes are not actually assigned on the product.
        # They are part of the product create.
        self.remote_value = self.get_remote_value()
        logger.debug(f"WooCommerceProductPropertyCreateFactory Remote value: {self.remote_value}")
        if self.get_value_only:
            self.remote_instance.remote_value = str(self.remote_value)
            logger.debug(f"WooCommerceProductPropertyCreateFactory Remote value id: {self.remote_instance.id}")
            self.remote_instance.save()
            return  # if we ony get the value we don't need to cotninue

        raise NotImplementedError("WooCommerceProductPropertyCreateFactory should be triggering a product-update after applying the attribute payload.")


class WooCommerceProductPropertyUpdateFactory(WooCommerceProductPropertyMixin, GetWoocommerceAPIMixin, RemoteProductPropertyUpdateFactory):
    def update_remote(self):
        # The attributes are not actually updated on the product.
        # They are set as part of the product
        raise NotImplementedError("WooCommerceProductPropertyUpdateFactory should be triggering a product-update after applying the attribute payload.")


class WooCommerceProductPropertyDeleteFactory(WooCommerceProductPropertyMixin, GetWoocommerceAPIMixin, RemoteProductPropertyDeleteFactory):
    def delete_remote(self):
        # The attributes are not actually updated on the product.
        # They are set as part of the product
        raise NotImplementedError("WooCommerceProductPropertyDeleteFactory should be triggering a product-update after applying the attribute payload.")
