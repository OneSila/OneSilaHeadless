from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceRemoteLanguage
from sales_channels.integrations.woocommerce.constants import EAN_CODE_WOOCOMMERCE_FIELD_NAME
from django.conf import settings
from media.models import Media
from sales_channels.integrations.woocommerce.models import WoocommerceGlobalAttribute, \
    WoocommerceCurrency
from sales_channels.integrations.woocommerce.constants import API_ATTRIBUTE_PREFIX
from properties.models import Property, ProductProperty
from django.db.models import Q
from sales_channels.factories.prices.prices import ToUpdateCurrenciesMixin

import logging
logger = logging.getLogger(__name__)


class SerialiserMixin:
    """
    Mixin providing common serialization methods for the woocommerce integration.
    """

    def serialize_response(self, response):
        return response or {}


class WoocommerceSalesChannelLanguageMixin:
    """expose the language of the sales channel"""
    @property
    def sales_channel_assign_language(self):
        """self.language doesnt seem to be available everywhere. So let's fetch it here."""
        language = WoocommerceRemoteLanguage.objects.get(
            sales_channel=self.sales_channel)
        return language.local_instance


class WoocommerceProductTypeMixin:
    """
    This mixin will give you access to:
    - is_woocommerce_simple_product
    - is_woocommerce_configurable_product
    - is_woocommerce_variant_product
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_woocomerce_product_types()

    def run(self, *args, **kwargs):
        self.set_woocomerce_product_types()
        super().run(*args, **kwargs)

    def get_local_product(self):
        return self.remote_product.local_instance

    def remote_product_is_variation(self):
        try:
            return self.is_variation
        except AttributeError as e:
            try:
                return self.remote_product.is_variation
            except AttributeError as e:
                logger.error(f"self.is_variation should exist. {e=}")

            return False

    def set_woocomerce_product_types(self):
        product = self.get_local_product()
        is_variation = self.remote_product_is_variation()

        self.is_woocommerce_simple_product = False
        self.is_woocommerce_configurable_product = False
        self.is_woocommerce_variant_product = False

        try:
            if product.is_configurable():
                self.is_woocommerce_configurable_product = True
            elif product.is_simple():
                if is_variation:
                    self.is_woocommerce_variant_product = True
                else:
                    self.is_woocommerce_simple_product = True
            else:
                raise ValueError(f"Product {product} is not configurable or simple. Configure other types.")
        except AttributeError as e:
            raise AttributeError(f"{self.__class__.__name__} {e=}") from e


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
        return value.value

    def get_multi_select_value(self, value):
        """Handles multi-select values."""
        return list({v.value for v in value.all()})

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


class WooCommerceProductAttributeMixin(WoocommerceSalesChannelLanguageMixin, WoocommerceProductTypeMixin, SerialiserMixin, WoocommerceRemoteValueConversionMixin):
    """
    This is the class used to populate all of the
    attributes on the products.

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

    def get_global_attribute_create_factory(self):
        from sales_channels.integrations.woocommerce.factories.properties import WooCommerceGlobalAttributeCreateFactory

        try:
            global_attribute_create_factory = self.global_attribute_create_factory
        except AttributeError:
            global_attribute_create_factory = WooCommerceGlobalAttributeCreateFactory

        return global_attribute_create_factory

    def slugified_internal_name(self, property):
        return f"{API_ATTRIBUTE_PREFIX}{property.internal_name}"

    def set_configurator_properties(self):
        product = self.get_local_product()
        product_rule = product.get_product_rule()

        # Get all variations
        variations = product.get_configurable_variations(active_only=True)

        # Get unique property values across variations
        self.configurator_properties = product.get_configurator_properties(product_rule=product_rule)
        self.configurator_property_ids = self.configurator_properties.values_list('id', flat=True)

    def get_configurator_property_values(self, prod_prop):
        """
        Get all unique property values for the configurator properties across all variations.
        Returns a dictionary mapping property IDs to lists of their values.
        """
        # FIXME: These values should be translated into the store language.
        prop = prod_prop.property
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
            if prop.type == Property.TYPES.SELECT:
                property_values.add(product_property.get_serialised_value())

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

    def get_configurable_product_attributes(self):
        product = self.get_local_product()
        return product.get_configurator_properties(public_information_only=False)

    def get_global_attribute(self, prod_prop):
        # We only get a global attribute if the property has add_to_filters set to True.
        prop = prod_prop.property
        if not prop.add_to_filters:
            return None

        try:
            ga = self.global_attribute_model_class.objects.get(
                local_instance=prop,
                sales_channel=self.sales_channel
            )
        except self.global_attribute_model_class.DoesNotExist:
            f = self.get_global_attribute_create_factory()(
                sales_channel=self.sales_channel,
                local_instance=prop
            )
            f.run()
            ga = f.remote_instance

        return ga

    def get_common_properties(self):
        product = self.get_local_product()
        variations = product.get_configurable_variations(active_only=True)
        configurator_properties = product.get_configurator_properties()

        common_product_properties = ProductProperty.objects.\
            filter(
                product__in=variations,
            ).\
            exclude(
                property__in=configurator_properties.values('property_id'),
            ).\
            distinct()
        return common_product_properties

    def get_variation_product_property_values(self, prod_prop):
        """
        This is specific behaviour for woocommerce
        we go and fetch all of the values for the variations.
        Not just the product itself.
        """
        prop = prod_prop.property
        product = self.get_local_product()
        variations = product.get_configurable_variations(active_only=True)

        properties = ProductProperty.objects.filter(
            product__in=variations,
            property=prop
        )

        # Workaround to ensure all values are unique becase you cannot
        # set() on a nested list. Instead convert into tuples.
        from itertools import chain

        raw_values = [i.get_serialised_value(language=self.sales_channel_assign_language) for i in properties]

        # Flatten all nested lists one level
        flattened = list(chain.from_iterable(
            v if isinstance(v, list) else [v] for v in raw_values
        ))

        # Remove duplicates while preserving order
        seen = set()
        final_values = []
        for item in flattened:
            if item not in seen:
                seen.add(item)
                final_values.append(item)

        return final_values

    def remove_duplicates(self, payload):
        seen = []
        unique_payload = []
        for item in payload:
            if item not in seen:
                seen.append(item)
                unique_payload.append(item)
        return unique_payload

    def apply_attribute_payload(self):
        """
        The payload for the attributes is different for simple, configurable and variant products.
        if you check out the tests_api.py file in the tests folder you will find a full exmaple
        of a working product.

        The main concideration is that the attribute payload is
        using singular vs plural form and
        global vs local attributes.

        As for attribute assignment. In OneSila we assign everything on the simple products.
        In Woocommerce all common attributes are assigned on the configurable products.
        Simple products only support the configurable differences.
        If you have attributes that are only used on simple product they most likely be ignored.

        Once you get that, the rest should be easy enough to understand.
        """
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
        product = self.get_local_product()
        logger.debug(f"Applying attribute payload for product: {product}")
        # ean_code = product.eancode_set.last()
        self.set_product_rule()
        self.set_product_properties_to_apply_payload()
        self.set_filterable_property_ids()

        # What is this product about?  How does it relate and what are the types?
        attribute_payload = []

        if self.is_woocommerce_variant_product:
            # Simple Variations (variation) use a singular form.
            # This is the attribute payload for the variation itelf.

            # # Firstly let's add the EAN Code.
            # # FIXME: This is the wrong implementation. There seems to be
            # # a direct field on the product admin pages with title: GTIN, UPC, EAN, or ISBN
            # if ean_code:
            #     attribute_payload.append({
            #         'name': 'EAN Code',
            #         'visible': True,
            #         'option': [ean_code.ean_code]
            #     })

            # It would seem that woocommerce doesnt have a problem with
            # Assigning too many attributes to a product. Even variations.
            # So let's just go ahead and do that.
            configurator_prod_props = product.productproperty_set.filter_for_configurator()
            variant_payload = []
            for prod_prop in configurator_prod_props.iterator():
                ga = self.get_global_attribute(prod_prop)
                if ga:
                    attribute_payload.append({
                        'id': ga.remote_id,
                        'visible': True,
                        'option': prod_prop.get_serialised_value(language=self.sales_channel_assign_language),
                    })
                else:
                    # NOTE: This does not support multi-values.
                    # Frankly it's really unclear how woocommerce even handles this.
                    # As this is technically not possible on a variation.
                    # on the other hand, a variation should not receive a
                    # a mult-value as it only recieves configurator values.
                    variant_payload.append({
                        'name': prod_prop.property.name,
                        'visible': True,
                        'option': prod_prop.get_serialised_value(language=self.sales_channel_assign_language),
                    })
            logger.debug(f"Variant payload: {variant_payload}")
            attribute_payload.extend(variant_payload)

        if self.is_woocommerce_simple_product or self.is_woocommerce_configurable_product:
            # Simple products use a plural form. So do configurable products.
            # This is the attribute payload then the simple product has been
            # directly assigned to the sales channel.
            # So we just go ahead and assign everything in one go.

            # Why do we also assign the configuraable properties here?
            # Because they actually only have the base product type, which
            # is also needed.  So to avoid writin it twice....
            product_properties = product.productproperty_set.all()
            simple_or_config_payload = []
            for prod_prop in product_properties.iterator():
                ga = self.get_global_attribute(prod_prop)

                # The simple product takes its own property values.
                # The configurable takes them from the varisations.
                if self.is_woocommerce_simple_product:
                    values = prod_prop.get_serialised_value(language=self.sales_channel_assign_language)
                elif self.is_woocommerce_configurable_product:
                    values = self.get_variation_product_property_values(prod_prop)

                if not isinstance(values, list):
                    values = [values]

                if ga:
                    remote_id = int(ga.remote_id)
                    simple_or_config_payload.append({
                        "id": remote_id,
                        "options": values,
                    })
                else:
                    simple_or_config_payload.append({
                        'name': prod_prop.property.name,
                        'visible': True,
                        'options': values
                    })
            logger.debug(f"Simple or config payload: {simple_or_config_payload}")
            attribute_payload.extend(simple_or_config_payload)

        if self.is_woocommerce_configurable_product:
            # The final case is a configurable product.
            # The individual property has already been assigned in an
            # earlier case. Now we find all of the common and uncommen properties
            # compile the list and add them to the payload.

            # Configurable products have no EAN code.. Skip that all together.

            # First step, get all of the variations possibilities.
            configurator_attributes = self.get_configurable_product_attributes()
            config_payload = []
            for prod_prop in configurator_attributes.iterator():
                ga = self.get_global_attribute(prod_prop)
                values = self.get_configurator_property_values(prod_prop)

                if not isinstance(values, list):
                    values = [values]

                remote_id = int(ga.remote_id)
                config_payload.append({
                    "id": remote_id,
                    "options": values,
                    "variation": True,
                })

            # Secondly populate all of the common properties. But
            # exclude the configurator properties. (done in method)
            common_properties = self.get_common_properties()
            common_payload = []
            for prod_prop in common_properties.iterator():
                ga = self.get_global_attribute(prod_prop)
                values = self.get_variation_product_property_values(prod_prop)

                if not isinstance(values, list):
                    values = [values]

                if ga:
                    remote_id = int(ga.remote_id)
                    common_payload.append({
                        "id": remote_id,
                        "options": values,
                    })
                else:
                    common_payload.append({
                        'name': prod_prop.property.name,
                        'visible': True,
                        'options': values
                    })
            logger.debug(f"Config payload: {config_payload}")
            attribute_payload.extend(config_payload)
            logger.debug(f"Common payload: {common_payload}")
            attribute_payload.extend(common_payload)

        self.payload['attributes'] = self.remove_duplicates(attribute_payload)
        return self.payload


class WooCommerceUpdateRemoteProductMixin(SerialiserMixin, GetWoocommerceAPIMixin):
    """
    This mixin is used to update the product in WooCommerce.
    It is most likely used in combination with the WooCommercePayloadMixin.
    but they are not together because some factories have slightly differnt needs
    in terms of update method naming.
    """

    def update_remote_product(self):
        if self.is_woocommerce_simple_product:
            return self.api.update_product(
                self.remote_product.remote_id,
                **self.payload
            )
        elif self.is_woocommerce_variable_product:
            return self.api.update_variable_product(
                self.remote_product.remote_parent_id,
                self.remote_product.remote_id,
                **self.payload
            )
        else:
            raise NotImplementedError("Unknown product type configuration.")


class WooCommercePayloadMixin(WooCommerceProductAttributeMixin, WoocommerceSalesChannelLanguageMixin, WoocommerceProductTypeMixin, ToUpdateCurrenciesMixin):
    remote_id_map = 'id'
    # Key is the local field, value is the remote field
    field_mapping = {
        'sku': 'sku',
        # The price fields are not really fields
        # but "magic" and get set during the payload build.
        # 'price': 'regular_price',
        # 'discount': 'sale_price',
        'name': 'name',
        'description': 'description',
        'short_description': 'short_description',
    }

    def get_local_product(self):
        return self.remote_product.local_instance

    def set_currency(self):
        if not hasattr(self, 'currency'):
            self.currency = WoocommerceCurrency.objects.get(
                sales_channel=self.sales_channel,
            ).local_instance
            self.currency_iso_code = self.currency.iso_code

    def apply_ean_code_payload(self):
        product = self.get_local_product()
        ean_code = product.eancode_set.last()

        try:
            self.payload[EAN_CODE_WOOCOMMERCE_FIELD_NAME] = ean_code.ean_code
        except AttributeError:
            # No EanCode, send empty payload
            self.payload[EAN_CODE_WOOCOMMERCE_FIELD_NAME] = ''

        return self.payload

    def get_image_url(self, media):
        import random
        import sys

        # Check if we're running in a test environment
        is_test = settings.TESTING

        logger.debug(f"Checking if in test environment: {is_test}")
        if is_test:
            fname = media.image_web.name.split('/')[-1]
            img_url = f"https://www.onesila.com/testing/{fname}"
            logger.debug(f"Replacing url to {img_url=} due to testing environment")
            return img_url

        return media.image_web_url

    def get_local_product(self):
        return self.remote_product.local_instance

    def get_sku(self):
        """Sets the SKU for the product or variation on the class."""
        product = self.get_local_product()
        return product.sku

    def apply_media_payload(self):
        # Woocom requires a full media payload for each product.
        # {
        #     "images": [
        #         {"src": "url"}
        #     ]
        # }
        product = self.get_local_product()
        # It seems that omitting the sku from the payload when
        # only images are updated can remove the sku from the product.
        # enforce the sku to ensure it is here at all times.
        self.payload['sku'] = self.get_sku()

        image_throughs = product.mediaproductthrough_set.filter(media__type=Media.IMAGE)
        logger.debug(f"apply_media_payload Found {image_throughs.count()} image_throughs for {product=}")

        payload = [{"src": self.get_image_url(i.media)} for i in image_throughs]
        self.payload['images'] = payload

        logger.debug(f"Media payload applied: {self.payload}")
        return self.payload

    def apply_price_payload(self):
        # Concidering that woocommerce only supports a single currency
        # then grabbing the currency in a static way is perfectly acceptable.
        currency_code = WoocommerceCurrency.objects.get(
            sales_channel=self.sales_channel).local_instance.iso_code
        price_info = self.price_data.get(currency_code, {})
        self.payload['regular_price'] = price_info.get('price', None)
        self.payload['sale_price'] = price_info.get('discount_price', None)
        return self.payload

    def apply_base_product_payload(self):
        """
        Customizes the payload for WooCommerce products
        """
        # Products must be created and updated with the attributes
        # included in the product payload.

        #
        # Apply the status payload.
        #
        product = self.get_local_product()
        if product.active:
            self.payload['status'] = 'publish'
            self.payload['catalog_visibility'] = 'visible'
        else:
            self.payload['status'] = 'draft'
            self.payload['catalog_visibility'] = 'hidden'

        #
        # Apply the woocommerce product types to the payloads.
        #
        if self.is_woocommerce_configurable_product:
            # This also needs the variations to be created.
            self.payload['type'] = 'variable'

        if self.is_woocommerce_simple_product:
            self.payload['type'] = 'simple'

        if self.is_woocommerce_variant_product:
            # No type is passed. Woocom takes care of it.
            # self.payload['type'] = 'variation'
            pass

        return self.payload

    def customize_payload(self):
        self.apply_base_product_payload()
        self.apply_ean_code_payload()
        self.apply_media_payload()
        self.apply_price_payload()
        self.apply_attribute_payload()
        return self.payload

    def run(self):
        self.set_currency()
        return super().run()

    # def apply_content_payload(self):
    #     # We need to build a manual payload. For that we need:
    #     language = self.sales_channel_assign_language
    #     product = self.get_local_product()
    #     translation = product.translations.get(language=language)

    #     self.payload['name'] = translation.name
    #     self.payload['description'] = translation.description
    #     self.payload['short_description'] = translation.short_description

    #     logger.debug(f"{self.__class__.__name__} payload: {self.payload}")
    #     return self.payload
