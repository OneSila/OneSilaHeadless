from django.utils.text import slugify
from magento.models import AttributeSet

from sales_channels.factories.mixins import RemoteInstanceCreateFactory, RemoteInstanceUpdateFactory, RemoteInstanceDeleteFactory
from sales_channels.factories.properties.properties import RemotePropertyCreateFactory, RemotePropertyDeleteFactory, RemotePropertySelectValueCreateFactory, \
    RemotePropertySelectValueUpdateFactory, RemotePropertySelectValueDeleteFactory, RemotePropertyUpdateFactory, RemoteProductPropertyCreateFactory, \
    RemoteProductPropertyDeleteFactory, RemoteProductPropertyUpdateFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models import MagentoProperty, MagentoPropertySelectValue
from properties.models import Property, ProductPropertyTextTranslation
from magento.models.product import ProductAttribute, Product

from sales_channels.integrations.magento2.models.properties import MagentoAttributeSet, MagentoAttributeSetAttribute, MagentoProductProperty
from sales_channels.models.sales_channels import RemoteLanguage


class MagentoPropertyCreateFactory(GetMagentoAPIMixin, RemotePropertyCreateFactory):
    remote_model_class = MagentoProperty
    remote_id_map = 'attribute_id'
    field_mapping = {
        'add_to_filters': 'is_filterable',
        'name': 'default_frontend_label'
    }

    api_package_name = 'product_attributes'
    api_method_name = 'create'

    FRONTEND_INPUT_MAP = {
        Property.TYPES.INT: ProductAttribute.TEXT,
        Property.TYPES.FLOAT: ProductAttribute.TEXT,
        Property.TYPES.TEXT: ProductAttribute.TEXT,
        Property.TYPES.DESCRIPTION: ProductAttribute.TEXTAREA,
        Property.TYPES.BOOLEAN: ProductAttribute.BOOLEAN,
        Property.TYPES.DATE: ProductAttribute.DATE,
        Property.TYPES.DATETIME: ProductAttribute.DATE,
        Property.TYPES.SELECT: ProductAttribute.SELECT,
        Property.TYPES.MULTISELECT: ProductAttribute.MULTISELECT
    }

    def customize_payload(self):
        """
        Customizes the payload to include the correct 'frontend_input' mapping and wraps it under 'data'.
        """
        # Add 'frontend_input' mapping
        self.payload['frontend_input'] = self.FRONTEND_INPUT_MAP.get(self.local_instance.type, ProductAttribute.TEXT)

        # we need to set it like this because of some issue with the order of the signals
        self.payload['attribute_code'] = slugify(self.local_instance.name).replace('-', '_')

        # Wrap the payload under the 'data' key as required by Magento's API
        self.payload = {'data': self.payload}
        return self.payload

    def serialize_response(self, response):
        return response.to_dict()

    def modify_remote_instance(self, response_data):
        self.remote_instance.attribute_code = response_data.get('data').get('attribute_code')


class MagentoPropertyUpdateFactory(GetMagentoAPIMixin, RemotePropertyUpdateFactory):
    remote_model_class = MagentoProperty
    create_factory_class = MagentoPropertyCreateFactory
    field_mapping = {
        'add_to_filters': 'is_filterable',
        'name': 'default_frontend_label'
    }

    def update_remote(self):
        self.magento_instance = self.api.product_attributes.by_code(self.remote_instance.attribute_code)
        for key, value in self.payload.items():
            setattr(self.magento_instance, key, value)

        self.magento_instance.save()

    def serialize_response(self, response):
        self.magento_instance.refresh()
        return self.magento_instance.to_dict()


class MagentoPropertyDeleteFactory(GetMagentoAPIMixin, RemotePropertyDeleteFactory):
    remote_model_class = MagentoProperty
    delete_remote_instance = True

    def delete_remote(self):
        magento_instance = self.api.product_attributes.by_code(self.remote_instance.attribute_code)
        return magento_instance.delete()

    def serialize_response(self, response):
        return response  # is True or False


class MagentoPropertySelectValueCreateFactory(GetMagentoAPIMixin, RemotePropertySelectValueCreateFactory):
    remote_model_class = MagentoPropertySelectValue
    remote_property_factory = MagentoPropertyCreateFactory
    remote_id_map = 'data__value'
    field_mapping = {
        'value': 'label'
    }

    api_package_name = 'product_attribute_options'
    api_method_name = 'create'

    def preflight_check(self):
        return not self.local_instance.property.is_product_type

    def preflight_process(self):
        super().preflight_process()
        self.magento_property = self.api.product_attributes.by_code(self.remote_property.attribute_code)
        self.api.product_attribute_options_attribute = self.magento_property

    def customize_payload(self):
        """
        Customizes the payload to include the correct data format required by Magento's API.
        """
        self.payload = {
            'label': self.local_instance.value,
        }
        self.payload = {'data': self.payload}
        return self.payload

    def serialize_response(self, response):
        return response.to_dict()


class MagentoPropertySelectValueUpdateFactory(GetMagentoAPIMixin, RemotePropertySelectValueUpdateFactory):
    remote_model_class = MagentoPropertySelectValue
    create_factory_class = MagentoPropertySelectValueCreateFactory

    field_mapping = {
        'value': 'label'
    }

    def preflight_check(self):
        return not self.local_instance.property.is_product_type

    def additional_update_check(self):
        # this we should do right before update so self.remote_instace is already there
        self.remote_property = self.remote_instance.remote_property.get_real_instance()
        self.magento_property = self.api.product_attributes.by_code(self.remote_property.attribute_code)
        self.api.product_attribute_options_attribute = self.magento_property

        return True

    def update_remote(self):
        self.magento_instance = self.api.product_attribute_options.by_id(self.remote_instance.remote_id)
        self.magento_instance.label = self.payload['label']
        self.magento_instance.save()

    def serialize_response(self, response):
        return self.magento_instance.to_dict()


class MagentoPropertySelectValueDeleteFactory(GetMagentoAPIMixin, RemotePropertySelectValueDeleteFactory):
    remote_model_class = MagentoPropertySelectValue

    def delete_remote(self):
        self.remote_property = self.remote_instance.remote_property.get_real_instance()
        self.magento_property = self.api.product_attributes.by_code(self.remote_property.attribute_code)
        self.api.product_attribute_options_attribute = self.magento_property

        self.magento_instance = self.api.product_attribute_options.by_id(self.remote_instance.remote_id)
        return self.magento_instance.delete()

    def serialize_response(self, response):
        return response


class RemoteValueMixin:
    def get_remote_value(self):
        # Get the local property type and value
        property_type = self.local_property.type
        value = self.local_instance.get_value()

        # Handle direct value types (int, float, boolean)
        if property_type in [Property.TYPES.INT, Property.TYPES.FLOAT]:
            return self.get_direct_value(value)

        if property_type == Property.TYPES.BOOLEAN:
            return self.get_boolean_value(value)

        # Handle SELECT and MULTISELECT types
        elif property_type == Property.TYPES.SELECT:
            return self.get_select_value(multiple=False)
        elif property_type == Property.TYPES.MULTISELECT:
            return self.get_select_value(multiple=True)

        elif property_type in [Property.TYPES.TEXT, Property.TYPES.DESCRIPTION]:
            return self.get_translated_values()

        # Handle DATE and DATETIME types with formatting
        elif property_type == Property.TYPES.DATE:
            return self.format_date(value)
        elif property_type == Property.TYPES.DATETIME:
            return self.format_datetime(value)

        # Default case if type is not recognized
        return None

    def get_direct_value(self, value):
        """Handles direct value types: int, float, boolean."""
        return value

    def get_boolean_value(self, value: bool) -> int:
        """Converts boolean values to 1 (True) or 0 (False) as required by Magento."""
        print('-------------------------------------------- ?')
        return 1 if value else 0

    def get_select_value(self, multiple):
        """Handles select and multiselect values."""
        if multiple:
            return ','.join(self.remote_select_values)
        else:
            # For single select
            return self.remote_select_values[0]

    def get_translated_values(self):
        """Retrieves translations and returns them as a dict or a single value."""
        # Retrieve all translations for the current property
        translations = ProductPropertyTextTranslation.objects.filter(product_property=self.local_instance)
        translation_count = translations.count()

        # Map local language to remote language code using RemoteLanguage model
        remote_languages = {rl.local_instance: rl.remote_code for rl in RemoteLanguage.objects.filter(
            sales_channel=self.sales_channel
        )}

        if self.get_value_only:
            # If get_value_only is True, return the value for the multi_tenant_company language
            multi_tenant_language = self.sales_channel.multi_tenant_company.language
            remote_code = remote_languages.get(multi_tenant_language)

            # Check if a translation exists for the multi_tenant_language
            default_translation = translations.filter(language=multi_tenant_language).first()

            if default_translation and remote_code:
                return default_translation.value_text if self.local_property.type == Property.TYPES.TEXT else default_translation.value_description

            # If the translation is not available or remote_code does not exist, return the first available translation
            first_translation = translations.first()
            return first_translation.value_text if first_translation and self.local_property.type == Property.TYPES.TEXT else first_translation.value_description

        # If only one translation exists, return it directly
        if translation_count == 1:
            translation = translations.first()
            return translation.value_text if self.local_property.type == Property.TYPES.TEXT else translation.value_description

        # Multiple translations: return them as a dictionary {remote_code: remote_value}
        translated_values = {}
        for translation in translations:
            language_code = translation.language
            remote_code = remote_languages.get(language_code)

            # Skip if no corresponding remote code found
            if not remote_code:
                continue

            # Choose the correct value type based on the property type
            remote_value = translation.value_text if self.local_property.type == Property.TYPES.TEXT else translation.value_description
            translated_values[remote_code] = remote_value

        return translated_values

    def format_date(self, date_value):
        """Formats date values to include time as '00:00:00' in Magento compatible format."""
        if date_value:
            # Formatting date to include time as 00:00:00
            return date_value.strftime('%d-%m-%Y 00:00:00')

    def format_datetime(self, datetime_value):
        """Formats datetime values to Magento compatible string format."""
        if datetime_value:
            return datetime_value.strftime('%d-%m-%Y %H:%M:%S')


class MagentoProductPropertyCreateFactory(GetMagentoAPIMixin, RemoteProductPropertyCreateFactory, RemoteValueMixin):
    remote_model_class = MagentoProductProperty
    remote_property_factory = MagentoPropertyCreateFactory
    remote_property_select_value_factory = MagentoPropertySelectValueCreateFactory

    def create_remote(self):
        self.remote_value = self.get_remote_value()
        if self.get_value_only:
            return  # if we ony get the value we don't need to cotninue

        self.magento_product: Product = self.api.products.by_sku(self.remote_product.remote_sku)
        if isinstance(self.remote_value, dict):
            for remote_code, value in self.remote_value.items():
                self.magento_product.update_custom_attributes({self.remote_property.attribute_code: value}, scope=remote_code)
        else:
            self.magento_product.update_custom_attributes({self.remote_property.attribute_code: self.remote_value})

    def serialize_response(self, response):
        return {self.remote_property.attribute_code: self.remote_value}

class MagentoProductPropertyUpdateFactory(GetMagentoAPIMixin, RemoteValueMixin, RemoteProductPropertyUpdateFactory):
    remote_model_class = MagentoProductProperty
    create_factory_class = MagentoProductPropertyCreateFactory
    remote_property_factory = MagentoPropertyCreateFactory
    remote_property_select_value_factory = MagentoPropertySelectValueCreateFactory

    def update_remote(self):
        self.magento_product: Product = self.api.products.by_sku(self.remote_product.remote_sku)
        if isinstance(self.remote_value, dict):
            for remote_code, value in self.remote_value.items():
                self.magento_product.update_custom_attributes({self.remote_property.attribute_code: value}, scope=remote_code)
        else:
            self.magento_product.update_custom_attributes({self.remote_property.attribute_code: self.remote_value})

    def serialize_response(self, response):
        return {self.remote_property.attribute_code: self.remote_value}

class MagentoProductPropertyDeleteFactory(GetMagentoAPIMixin, RemoteProductPropertyDeleteFactory):
    remote_model_class = MagentoProductProperty
    delete_remote_instance = True

    def delete_remote(self):
        self.magento_product: Product = self.api.products.by_sku(self.remote_instance.remote_product.remote_sku)
        self.magento_product.update_custom_attributes({self.remote_instance.remote_property.attribute_code: None})

    def serialize_response(self, response):
        return True

class EnsureMagentoAttributeSetAttributesMixin:

    def create_existing_attributes(self, attribute_set_mirror_instance: MagentoAttributeSet, attribute_set_magento_instance: AttributeSet):
        """
        Manages the creation and association of attributes in the Magento attribute set.
        Returns a list of existing attribute set attribute remote IDs.
        """
        rule = attribute_set_mirror_instance.local_instance
        existing_attribute_set_attributes_ids = []

        for item in rule.items.all():
            # Handle existing attributes and add them to the list if found
            if self.attribute_set_attribute_exists(item, attribute_set_mirror_instance, existing_attribute_set_attributes_ids):
                continue

            # Process attribute creation and association with the Magento attribute set
            self.process_attribute_creation(
                item,
                attribute_set_mirror_instance,
                attribute_set_magento_instance,
                existing_attribute_set_attributes_ids
            )

        return existing_attribute_set_attributes_ids

    def attribute_set_attribute_exists(self, item, attribute_set_mirror_instance, existing_attribute_set_attributes_ids):
        """
        Checks if the MagentoAttributeSetAttribute already exists for the given item.
        Adds the remote ID of the associated MagentoProperty to the existing_attribute_set_attributes_ids list if found.
        Returns True if the attribute exists, otherwise False.
        """
        try:
            attribute_mirror = MagentoAttributeSetAttribute.objects.get(
                local_instance=item,
                magento_rule=attribute_set_mirror_instance
            )

            # Add the remote_id of the MagentoProperty to the existing_attribute_set_attributes_ids list
            existing_attribute_set_attributes_ids.append(attribute_mirror.remote_property.remote_id)
            return True
        except (MagentoAttributeSetAttribute.DoesNotExist, MagentoProperty.DoesNotExist):
            return False

    def process_attribute_creation(self, item, attribute_set_mirror_instance, attribute_set_magento_instance, existing_attribute_set_attributes_ids):
        """
        Processes the creation of the Magento attribute for the given item.
        Creates the MagentoProperty if it does not exist and associates it with the attribute set in Magento.
        """
        # Retrieve or create the MagentoProperty associated with the item
        remote_property = self.get_or_create_magento_property(item, attribute_set_mirror_instance)

        attribute_set_magento_instance.add_attribute_set_attribute(
            attribute_set_mirror_instance.group_remote_id,
            remote_property.attribute_code,
            item.sort_order
        )

        # Create the MagentoAttributeSetAttribute
        self.create_magento_attribute_set_attribute(item, attribute_set_mirror_instance, remote_property)

        # Track the remote_id of the newly created attribute
        existing_attribute_set_attributes_ids.append(remote_property.remote_id)

    def get_or_create_magento_property(self, item, attribute_set_mirror_instance):
        """
        Retrieves the MagentoProperty for the specified item and sales channel.
        If it does not exist, it creates a new MagentoProperty using MagentoPropertyCreateFactory.
        """
        property_instance = item.property
        try:
            return MagentoProperty.objects.get(
                local_instance=property_instance,
                sales_channel=attribute_set_mirror_instance.sales_channel
            )
        except MagentoProperty.DoesNotExist:
            # Create the MagentoProperty if it doesn't exist
            property_create_factory = MagentoPropertyCreateFactory(
                sales_channel=attribute_set_mirror_instance.sales_channel,
                local_instance=property_instance
            )
            property_create_factory.run()
            return property_create_factory.remote_instance

    def create_magento_attribute_set_attribute(self, item, attribute_set_mirror_instance, remote_property):
        """
        Creates a MagentoAttributeSetAttribute instance for the given item, attribute set, and remote property.
        """
        MagentoAttributeSetAttribute.objects.create(
            local_instance=item,
            magento_rule=attribute_set_mirror_instance,
            remote_id=remote_property.remote_id,
            remote_property=remote_property,
            sales_channel=attribute_set_mirror_instance.sales_channel,
            multi_tenant_company=attribute_set_mirror_instance.multi_tenant_company
        )


class MagentoAttributeSetCreateFactory(GetMagentoAPIMixin, RemoteInstanceCreateFactory, EnsureMagentoAttributeSetAttributesMixin):
    remote_model_class = MagentoAttributeSet
    remote_id_map = 'attribute_set_id'
    field_mapping = {
        'product_type__value': 'attribute_set_name'
    }

    api_package_name = 'product_attribute_set'
    api_method_name = 'create'

    def customize_payload(self):
        """
        Customizes the payload to include the correct data format required by Magento's API.
        """
        self.payload['skeleton_id'] = 4  # @TODO: FIND A BETTER WAY TO DO THIS
        self.payload = {'data': self.payload}
        return self.payload

    def serialize_response(self, response):
        return response.to_dict()

    def set_attribute_set_magento_instance(self):
        self.attribute_set_magento_instance = self.api.product_attribute_set.by_id(self.remote_instance.remote_id)

    def set_group_id(self):
        group = self.attribute_set_magento_instance.get_or_create_group_by_name('OneSila')
        self.remote_instance.group_remote_id = group.attribute_group_id
        self.remote_instance.save()

    def post_create_process(self):
        self.set_attribute_set_magento_instance()
        self.set_group_id()
        self.create_existing_attributes(self.remote_instance, self.attribute_set_magento_instance)


class MagentoAttributeSetUpdateFactory(GetMagentoAPIMixin, RemoteInstanceUpdateFactory, EnsureMagentoAttributeSetAttributesMixin):
    remote_model_class = MagentoAttributeSet
    field_mapping = {
        'product_type__value': 'attribute_set_name'
    }

    def __init__(self, sales_channel, local_instance, update_name_only=False, api=None, remote_instance=None):
        super().__init__(sales_channel, local_instance, api=api, remote_instance=remote_instance)
        self.update_name_only = update_name_only

    def update_remote(self):
        self.attribute_set_magento_instance = self.api.product_attribute_set.by_id(self.remote_instance.remote_id)
        for key, value in self.payload.items():
            setattr(self.attribute_set_magento_instance, key, value)

        self.attribute_set_magento_instance.save()

    def needs_update(self):
        return True  # we don't need to compare the payloads since this is sent by us when something actually changes

    def serialize_response(self, response):
        return self.attribute_set_magento_instance.to_dict()

    def remove_unnecessary_attributes(self, existing_ids):
        """
        Removes attributes from the Magento attribute set that are no longer in the existing list.
        Deletes the corresponding MagentoAttributeSetAttribute mirror instance.
        """

        # Fetch all MagentoAttributeSetAttribute instances related to the remote instance
        attribute_set_attributes = MagentoAttributeSetAttribute.objects.filter(magento_rule=self.remote_instance)

        for attribute in attribute_set_attributes:
            # Check if the remote_property.remote_id is not in the existing_ids
            if attribute.remote_property.remote_id not in existing_ids:
                self.attribute_set_magento_instance.remove_attribute_set_attribute(attribute.remote_property.attribute_code)
                attribute.delete()

    def post_update_process(self):
        if self.update_name_only:
            return

        existing_ids = self.create_existing_attributes(self.remote_instance, self.attribute_set_magento_instance)
        self.remove_unnecessary_attributes(existing_ids)


class MagentoAttributeSetDeleteFactory(GetMagentoAPIMixin, RemoteInstanceDeleteFactory):
    remote_model_class = MagentoAttributeSet
    delete_remote_instance = True

    def delete_remote(self):
        magento_instance = self.api.product_attribute_set.by_id(self.remote_instance.remote_id)
        return magento_instance.delete()

    def serialize_response(self, response):
        return response  # is True or False
