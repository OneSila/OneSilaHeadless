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
from django.db.models import Q

import logging
logger = logging.getLogger(__name__)


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
        product_properties = ProductProperty.objects.\
            filter(
                product=product,
            )
        logger.debug(f"Found {product_properties.count()} product_properties for {product=}")

        attribute_payload = []
        #
        # Step 1: Add the EAN Codes:
        #
        # It seems we can have a set of EAN Codes.
        # Lets grab the last one for now.
        ean_code = product.eancode_set.last()
        if ean_code:
            attribute_payload.append({
                'name': 'EAN Code',
                'visible': True,
                'variation': False,
                'options': [ean_code.ean_code]
            })
        #
        # Step 2: Add the Global Attributes:
        #
        # We want both filterable and product-type properties to go here.
        properties_ids_for_global_attributes = product_properties.\
            filter(Q(property__add_to_filters=True) | Q(property__is_product_type=True)).\
            distinct().\
            values_list('id', flat=True)
        logger.debug(f"Found {properties_ids_for_global_attributes.count()} properties_ids_for_global_attributes for {product=}")

        woocommerce_global_attributes = self.global_attribute_model_class.objects.\
            filter(local_instance__id__in=properties_ids_for_global_attributes)
        logger.debug(f"Found {woocommerce_global_attributes.count()} woocommerce_global_attributes for {product=}")

        for ga in woocommerce_global_attributes.iterator():
            prop = ga.local_instance
            prop_values = [str(i.get_value()) for i in product_properties.filter(property=prop)]
            attribute_payload.append({
                "id": ga.remote_id,
                "name": prop.name,
                "slug": self.slugified_internal_name(prop),
                "visible": prop.is_public_information,
                "variation": False,  # May need fixing as it seems like a configurator thing.
                "options": prop_values,
            })
        #
        # Step 3: Add the Local Attributes:
        #
        properties_ids_for_local_attributes = product_properties.\
            exclude(property__in=properties_ids_for_global_attributes)
        properties_for_local_attributes = Property.objects.filter(id__in=properties_ids_for_local_attributes)
        logger.debug(f"Found {properties_for_local_attributes.count()} properties_for_local_attributes for {product=}")
        logger.debug(f"Found {properties_for_local_attributes.count()} properties_for_local_attributes for {product=}")

        for prop in properties_for_local_attributes.iterator():
            prop_values = [str(i.get_value()) for i in product_properties.filter(property=prop)]
            attribute_payload.append({
                "name": prop.name,
                "variation": False,
                "options": prop_values
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


class WooCommerceProductPropertyMixin(WooCommerceProductAttributeMixin, SerialiserMixin):
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
