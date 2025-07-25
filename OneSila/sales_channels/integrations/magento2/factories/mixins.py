from magento import get_api
from collections import defaultdict
from properties.models import Property, ProductPropertyTextTranslation
from sales_channels.integrations.magento2.models.properties import MagentoAttributeSet, MagentoAttributeSetAttribute, MagentoProperty
from magento.models import AttributeSet

from sales_channels.integrations.magento2.models.sales_channels import MagentoRemoteLanguage
from sales_channels.models.sales_channels import RemoteLanguage, SalesChannelViewAssign


class GetMagentoAPIMixin:
    def get_api(self):
        """
        Retrieves the Magento API client configured for the specific sales channel.
        """
        return get_api(
            domain=self.sales_channel.hostname,
            username=self.sales_channel.host_api_username,
            password=self.sales_channel.host_api_key,
            api_key=self.sales_channel.host_api_key,
            local=not self.sales_channel.verify_ssl,
            user_agent=None,
            authentication_method=self.sales_channel.authentication_method,
            strict_mode=True
        )


class MagentoEntityNotFoundGeneralErrorMixin:

    def is_duplicate_error(self, error):
        return "already exists" in str(error)


class MagentoTranslationMixin:
    def get_magento_languages(self, product=None, language=None):
        """
        Returns a grouped structure of remote languages by local language code.

        If a product is provided, filters only the sales channel views assigned to it.
        """
        remote_language_qs = MagentoRemoteLanguage.objects.filter(
            sales_channel=self.sales_channel,
            store_view_code__isnull=False,
            local_instance__isnull=False
        )

        if product:
            sales_views_ids = SalesChannelViewAssign.objects.filter(
                sales_channel=self.sales_channel,
                product=product
            ).values_list('sales_channel_view_id', flat=True)

            remote_language_qs = remote_language_qs.filter(
                sales_channel_view_id__in=sales_views_ids
            )

        if language:
            remote_language_qs = remote_language_qs.filter(local_instance=language)

        languages_by_local = defaultdict(list)
        for rl in remote_language_qs:
            languages_by_local[rl.local_instance].append(rl)

        return languages_by_local

    def get_frontend_labels(self, translations, value_field, language=None):
        """
        Prepares a list of frontend labels to be used in Magento API.

        :param translations: Queryset of ProductTranslation
        :param value_field: Field name from translation to use as label
        :return: List of dicts with label and store_id
        """
        frontend_labels = []
        remote_languages = self.get_magento_languages(language=language)

        for translation in translations:
            language_code = translation.language
            magento_langs = remote_languages.get(language_code, [])

            for magento_language in magento_langs:
                label = getattr(translation, value_field, None)
                if label:
                    frontend_labels.append({
                        'label': label,
                        'store_id': magento_language.remote_id
                    })

        return frontend_labels


class RemoteValueMixin(MagentoTranslationMixin):
    """ Convert OneSila payloads to Magento expected format."""

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
            sales_channel=self.sales_channel)}

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
        language_to_remote_languages = self.get_magento_languages(product=self.local_instance.product, language=self.language)
        for translation in translations:
            value = (
                translation.value_text if self.local_property.type == Property.TYPES.TEXT
                else translation.value_description
            )
            for lang in language_to_remote_languages.get(translation.language, []):
                translated_values[lang.store_view_code] = value

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
        existing_attribute_set_attributes_ids.append(str(remote_property.remote_id))

    def get_or_create_magento_property(self, item, attribute_set_mirror_instance):
        """
        Retrieves the MagentoProperty for the specified item and sales channel.
        If it does not exist, it creates a new MagentoProperty using MagentoPropertyCreateFactory.
        """
        from sales_channels.integrations.magento2.factories.properties import MagentoPropertyCreateFactory

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
