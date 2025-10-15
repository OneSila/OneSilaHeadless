from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceRemoteLanguage
from sales_channels.integrations.woocommerce.constants import EAN_CODE_WOOCOMMERCE_FIELD_NAME
from sales_channels.exceptions import ConfiguratorPropertyNotFilterable
from django.conf import settings
from media.models import Media, MediaProductThrough
from sales_channels.integrations.woocommerce.models import WoocommerceGlobalAttribute, \
    WoocommerceCurrency
from sales_channels.integrations.woocommerce.constants import API_ATTRIBUTE_PREFIX
from properties.models import Property, ProductProperty
from django.db.models import Q
from sales_channels.factories.prices.prices import ToUpdateCurrenciesMixin
from django.utils.translation import gettext as _

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
            try:
                is_variation = self.is_variation
                return is_variation
            except AttributeError as e:
                is_variation = self.remote_product.is_variation
                return is_variation
        except Exception as e:
            raise ValueError(f"Could not determine if remote product is a variation.") from e

    def set_woocomerce_product_types(self):
        product = self.get_local_product()
        is_variation = self.remote_product_is_variation()

        self.is_woocommerce_simple_product = False
        self.is_woocommerce_configurable_product = False
        self.is_woocommerce_variant_product = False

        try:
            if product.is_configurable():
                self.is_woocommerce_configurable_product = True
            else:
                if is_variation:
                    self.is_woocommerce_variant_product = True
                else:
                    self.is_woocommerce_simple_product = True
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
        return str(value)

    def get_float_value(self, value):
        """Handles float value types."""
        return str(value)

    def get_boolean_value(self, value: bool) -> str:
        """Converts boolean values to translated strings for WooCommerce."""
        return _("Yes") if value else _("No")

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

    def get_global_attribute(self, prod_prop, *, raise_if_none: bool = False):
        # We only get a global attribute if the property has add_to_filters set to True.
        prop = prod_prop.property
        if not prop.add_to_filters:
            if raise_if_none:
                prop_name = getattr(prop, "name", None)
                identifier = prop_name or f"ID={getattr(prop, 'id', 'UNKNOWN')}"
                raise ConfiguratorPropertyNotFilterable(
                    f"Property '{identifier}' is not marked as filterable and cannot be used as a configurator attribute."
                )
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

    def _stringify_attribute_option(self, value):
        if isinstance(value, list):
            return [self._stringify_attribute_option(item) for item in value]
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return str(value)

    def get_serialised_woocommerce_value(self, prod_prop):
        value = prod_prop.get_serialised_value(language=self.sales_channel_assign_language)
        if prod_prop.property.type == Property.TYPES.BOOLEAN:
            value = self.get_boolean_value(value)
        return self._stringify_attribute_option(value)

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

        raw_values = [self.get_serialised_woocommerce_value(i) for i in properties]

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
                        'option': self.get_serialised_woocommerce_value(prod_prop),
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
                        'option': self.get_serialised_woocommerce_value(prod_prop),
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
                    values = self.get_serialised_woocommerce_value(prod_prop)
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
                ga = self.get_global_attribute(prod_prop, raise_if_none=True)
                values = self.get_configurator_property_values(prod_prop)

                if not isinstance(values, list):
                    values = [values]

                if ga is None:
                    raise ValueError(
                        f"Missing global attribute for property ID={prod_prop.id}, "
                        f"property='{getattr(prod_prop.property, 'name', 'UNKNOWN')}'"
                    )

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
        if self.is_woocommerce_variant_product:
            parent_id = self.remote_product.remote_parent_product.remote_id
            variant_id = self.remote_product.remote_id
            return self.api.update_product_variation(parent_id, variant_id, **self.payload)
        else:
            product_id = self.remote_product.remote_id
            return self.api.update_product(product_id, **self.payload)


class WooCommercePayloadMixin(WooCommerceProductAttributeMixin, WoocommerceSalesChannelLanguageMixin, WoocommerceProductTypeMixin, ToUpdateCurrenciesMixin):
    remote_id_map = 'id'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_local_product(self):
        return self.remote_product.local_instance

    def set_currency(self):
        if not hasattr(self, 'currency'):
            self.currency = WoocommerceCurrency.objects.get(sales_channel=self.sales_channel).local_instance
            self.currency_iso_code = self.currency.iso_code

    def apply_content_payload(self):
        """Set name, description and short_description based on translations."""

        product = self.get_local_product()
        lang = getattr(self, "language", None) or self.sales_channel_assign_language

        channel_translation = product.translations.filter(
            language=lang,
            sales_channel=self.sales_channel,
        ).first()

        default_translation = product.translations.filter(
            language=lang,
            sales_channel=None,
        ).first()

        name = None
        description = None
        short_description = None

        if channel_translation:
            name = channel_translation.name or None
            description = channel_translation.description
            if description == "<p><br></p>":
                description = ""
            short_description = channel_translation.short_description

        if not name and default_translation:
            name = default_translation.name

        if (not description) and default_translation:
            description = default_translation.description
            if description == "<p><br></p>":
                description = ""

        if (not short_description) and default_translation:
            short_description = default_translation.short_description

        if short_description == "<p><br></p>":
            short_description = ""

        if name is not None:
            self.payload["name"] = name
        if description is not None:
            self.payload["description"] = description
        if short_description is not None:
            self.payload["short_description"] = short_description

        return self.payload

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
        sales_channel = getattr(self, "sales_channel", None)
        image_throughs = (
            MediaProductThrough.objects.get_product_images(
                product=product,
                sales_channel=sales_channel,
            )
            .filter(media__type=Media.IMAGE)
            .select_related("media")
        )
        payload = [{"src": self.get_image_url(i.media)} for i in image_throughs]
        self.payload['images'] = payload
        return self.payload

    def apply_price_payload(self):
        from sales_channels.integrations.woocommerce.models import WoocommercePrice, WoocommerceProduct
        # Concidering that woocommerce only supports a single currency
        # then grabbing the currency in a static way is perfectly acceptable.
        currency_code = WoocommerceCurrency.objects.get(
            sales_channel=self.sales_channel).local_instance.iso_code
        price_info = self.price_data.get(currency_code, {})
        self.payload['regular_price'] = price_info.get('price', None)
        self.payload['sale_price'] = price_info.get('discount_price', None)

        WoocommercePrice.objects.get_or_create(
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
        )
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
        self.payload['sku'] = product.sku

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
        self.apply_content_payload()
        return self.payload

    def run(self):
        self.set_currency()
        return super().run()
