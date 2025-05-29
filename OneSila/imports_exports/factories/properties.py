import logging
from django.db.models.fields.related import ManyToManyField
from datetime import datetime
from types import SimpleNamespace
from imports_exports.factories.mixins import ImportOperationMixin, AbstractImportInstance
from llm.factories.property_type_detector import DetectPropertyTypeLLM
from properties.models import Property, PropertyTranslation, PropertySelectValue, PropertySelectValueTranslation, \
    ProductPropertiesRule, ProductPropertiesRuleItem, ProductProperty, ProductPropertyTextTranslation


logger = logging.getLogger(__name__)


class PropertyImportUsingInternalName(ImportOperationMixin):
    get_identifiers = ['internal_name', 'type']


class PropertyImportUsingTranslationName(ImportOperationMixin):
    get_using_translation = True
    translation_get_value = 'property'
    get_identifiers = ['type']
    get_translation_identifiers = ['name']


class PropertySelectValueImport(ImportOperationMixin):
    get_using_translation = True
    allow_edit = False
    translation_get_value = 'propertyselectvalue'
    get_identifiers = ['property']
    get_translation_identifiers = ['value', 'propertyselectvalue__property']


class ProductPropertiesRuleImport(ImportOperationMixin):
    get_identifiers = ['product_type']


class ProductPropertiesRuleItemImport(ImportOperationMixin):
    get_identifiers = ['rule', 'property']

    def update_instance(self):
        """
        Prevents downgrading from REQUIRED/CONFIGURATOR types to OPTIONAL.
        """
        to_save = False

        for key in self.import_instance.updatable_fields:
            if not hasattr(self.import_instance, key):
                continue

            val = getattr(self.import_instance, key)
            field = self.instance._meta.get_field(key)

            if key == 'type':
                original = getattr(self.instance, key)

                protected_types = {
                    ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
                    ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR,
                    ProductPropertiesRuleItem.REQUIRED,
                }

                if original in protected_types and val == ProductPropertiesRuleItem.OPTIONAL:
                    logger.info(f"Skipping downgrade of type from {original} to OPTIONAL for {self.instance}")
                    continue

            if isinstance(field, ManyToManyField):
                current_val_ids = list(getattr(self.instance, key).values_list('id', flat=True))
                new_val_ids = list(val.values_list('id', flat=True))

                if set(current_val_ids) != set(new_val_ids):
                    getattr(self.instance, key).set(val)
                    logger.debug(f"Updated many-to-many field '{key}': {current_val_ids} -> {new_val_ids}")
            else:
                current_val = getattr(self.instance, key, None)
                if current_val != val:
                    setattr(self.instance, key, val)
                    to_save = True
                    logger.debug(f"Updated field '{key}': {current_val} -> {val}")

        if to_save:
            self.instance.save()
            logger.info(f"Local instance updated: {self.instance}")


class ProductPropertyImport(ImportOperationMixin):
    get_identifiers = ['product', 'property']


class TranslatedProductPropertyImport(ImportOperationMixin):
    get_using_translation = True
    allow_edit = False
    allow_translation_edit = True
    translation_get_value = 'product_property'
    get_translation_identifiers = ['product_property__product', 'product_property__property']
    get_identifiers = ['product', 'property']


class ImportPropertyInstance(AbstractImportInstance):
    """
    Abstract base class for processing an import property instance from a dict.

    Expected data keys (with defaults for optionals):
      - type: Optional; if missing or empty, will be detected via detect_type().
      - internal_name: Optional; however, either internal_name or name must be provided.
      - name: Optional; however, either name or internal_name must be provided.
      - is_public_information: Optional; defaults to True.
      - add_to_filters: Optional; defaults to True.
      - has_image: Optional; defaults to False.

    Example data dictionaries:

    1. Fully specified data:
       {
           "name": "Color",
           "internal_name": "color",
           "type": "TEXT",
           "is_public_information": True,
           "add_to_filters": True,
           "has_image": False
           "translations": [
            { "language": "en", "name": "Material" },
            { "language": "nl", "name": "Materiaal" },
            { "language": "fr", "name": "Matériau" }
          ]
       }

    2. Minimal data with type provided:
       {
           "name": "Size",
       }

      {
           "internal_name": "size",
       }

    3. Data without type (triggers type detection):
       {
           "internal_name": "weight",
           "is_public_information": False,
           "add_to_filters": False,
           "has_image": False
       }
    """
    ALLOWED_TYPES = [choice[0] for choice in Property.TYPES.ALL]

    def __init__(self, data: dict, import_process=None, instance=None):
        super().__init__(data, import_process, instance)

        # make sure we only use the needed values
        self.set_field_if_exists('name')
        self.set_field_if_exists('internal_name')
        self.set_field_if_exists('type')
        self.set_field_if_exists('is_public_information')
        self.set_field_if_exists('add_to_filters')
        self.set_field_if_exists('has_image')
        self.set_field_if_exists('translations')

        # First, validate required keys and boolean field types (ignoring 'type').
        self.validate()

        # If 'type' is missing or empty, detect it.
        if not hasattr(self, 'type'):
            self.detect_type()

        # Now validate that the property type is one of the allowed types.
        self.validate_type()

        # initiate the default import factory
        self.factory_class = PropertyImportUsingTranslationName

    @property
    def local_class(self):
        return Property

    @property
    def local_translation_class(self):
        return PropertyTranslation

    @property
    def updatable_fields(self):
        return ['is_public_information', 'add_to_filters', 'has_image']

    def detect_type(self):
        """
        Detects and returns the property type if not provided.
        Concrete implementations must override this method.
        """
        llm = DetectPropertyTypeLLM(self.data, self.multi_tenant_company)
        self.type = llm.detect_type()

    def validate(self):
        """
        Validates that at least one of 'internal_name' or 'name' is provided
        as an instance attribute and that the boolean fields in updatable_fields
        have boolean values.
        """
        if not (hasattr(self, 'internal_name') or hasattr(self, 'name')):
            raise ValueError("Either 'internal_name' or 'name' must be provided.")

        for key in self.updatable_fields:
            if hasattr(self, key):
                value = getattr(self, key)
                if not isinstance(value, bool):
                    raise ValueError(f"Field '{key}' must be a boolean value.")

    def validate_type(self):
        """
        Validates that the property type (stored as an attribute 'type') is one of the allowed types.
        """
        prop_type = getattr(self, 'type', None)
        if prop_type not in self.ALLOWED_TYPES:
            raise ValueError(
                f"Invalid property type: {prop_type}. Allowed types are: {self.ALLOWED_TYPES}")

    def pre_process_logic(self):
        # Decide which factory to use based on the data.
        if hasattr(self, 'internal_name'):
            self.factory_class = PropertyImportUsingInternalName
        else:
            self.factory_class = PropertyImportUsingTranslationName

    def process_logic(self):

        # Instantiate the factory, providing the mandatory import_process.
        fac = self.factory_class(self, self.import_process, instance=self.instance)
        fac.run()

        # Save the created/updated instance.
        self.instance = fac.instance

        # Only create a default translation if:
        # - the instance was just created
        # - and no valid translations were passed
        if fac.created and not (hasattr(self, 'translations') and len(self.translations) > 0):
            self.create_translation()

    def create_translation(self):

        name = None
        if hasattr(self, 'name'):
            name = self.name

        if name is None and hasattr(self, 'internal_name'):
            name = self.internal_name.replace('_', ' ').title()

        self.translation, _ = PropertyTranslation.objects.get_or_create(
            multi_tenant_company=self.instance.multi_tenant_company,
            language=self.language,
            property=self.instance,
            name=name,
        )

    def post_process_logic(self):

        if not hasattr(self, 'translations'):
            return

        for translation in self.translations:
            language = translation.get('language', None)
            name = translation.get('name', None)

            if not language or not name:
                continue

            translation_object, created = PropertyTranslation.objects.get_or_create(
                multi_tenant_company=self.instance.multi_tenant_company,
                language=language,
                property=self.instance
            )

            # Update name if changed
            if translation_object.name != name:
                translation_object.name = name
                translation_object.save()


class ImportPropertySelectValueInstance(AbstractImportInstance):
    """
    Import instance for PropertySelectValue.

    Expected data keys:
      - value: The select value to be imported.
      - property_data: (Optional) A dict for importing the Property if no property is provided.
      - translations: (Optional) A list of translations with 'language' and 'value' keys.

    Optionally, if the property already exists, the data may contain a 'property' key.
    """

    def __init__(self, data: dict, import_process=None, property=None, instance=None):
        super().__init__(data, import_process, instance)
        self.property = property

        self.set_field_if_exists('value')
        self.set_field_if_exists('property_data')
        self.set_field_if_exists('translations')

        self.validate()
        self._set_property_import_instance()

    @property
    def local_class(self):
        return PropertySelectValue

    @property
    def local_translation_class(self):
        return PropertySelectValueTranslation

    def validate(self):
        """
        Validate that the 'value' key exists.
        """
        if not hasattr(self, 'value'):
            raise ValueError("The 'value' field is required.")

        if not getattr(self, 'property_data', None) and not self.property:
            raise ValueError("Either a 'property' or 'property_data' must be provided.")

    def _set_property_import_instance(self):
        if not self.property:
            self.property_import_instance = ImportPropertyInstance(self.property_data, self.import_process)

    def pre_process_logic(self):

        # If the property is not provided, run the property import.
        if not self.property:
            self.property_import_instance.process()
            self.property = self.property_import_instance.instance

        # we need this so our identifier propertyselectvalue__property will work
        self.propertyselectvalue = SimpleNamespace(property=self.property)

    def process_logic(self):
        """
        Processes the select value import.

        - If a Property instance is already provided (via 'property'), use it.
        - Otherwise, import the Property using 'property_data' via ImportPropertyInstance.
        - Then, create or update the PropertySelectValue using the provided 'value'.
        """
        fac = PropertySelectValueImport(self, self.import_process, instance=self.instance)
        fac.run()

        # Save the created/updated instance.
        self.instance = fac.instance

        if fac.created and not (hasattr(self, 'translations') and len(self.translations) > 0):
            self.create_translation()

    def create_translation(self):

        self.translation = PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.instance.multi_tenant_company,
            language=self.language,
            propertyselectvalue=self.instance,
            value=self.value
        )

    def post_process_logic(self):
        """
        Handles additional translations after main instance is created.
        """

        if not hasattr(self, 'translations'):
            return

        for translation in self.translations:
            language = translation.get('language')
            value = translation.get('value')

            if not language or not value:
                continue

            translation_object, _ = PropertySelectValueTranslation.objects.get_or_create(
                multi_tenant_company=self.instance.multi_tenant_company,
                language=language,
                propertyselectvalue=self.instance
            )

            if translation_object.value != value:
                translation_object.value = value
                translation_object.save()


class ImportProductPropertiesRuleInstance(AbstractImportInstance):
    """
    Import instance for ProductPropertiesRule.

    Expected data keys:
      - value: The select value to be imported.
      - require_ean_code: Optional boolean indicating whether an EAN code is required.
      - items: Optional the data for

    """

    def __init__(self, data: dict, import_process=None, product_type=None, instance=None):
        super().__init__(data, import_process, instance)

        # an existing Property instance, if provided
        self.product_type = product_type

        # Set instance attributes only if they exist in the input data.
        self.set_field_if_exists('value')
        self.set_field_if_exists('require_ean_code')
        self.set_field_if_exists('items')

        # Validate required keys:
        self.validate()

        # we do this here because we will also validate the data on the ImportPropertySelectValueInstance
        self._set_property_import_instance()

    @property
    def local_class(self):
        return ProductPropertiesRule

    @property
    def updatable_fields(self):
        return ['require_ean_code']

    def validate(self):

        if not hasattr(self, 'value'):
            raise ValueError("The 'value' field is required.")

        if hasattr(self, 'items') and not isinstance(self.items, list):
            raise ValueError("The 'items' field must be a list.")

    def _set_property_import_instance(self):

        # If the property is not provided, run the property import.
        if not self.product_type:
            product_type_property = Property.objects.get(multi_tenant_company=self.multi_tenant_company,
                                                         is_product_type=True)

            self.property_select_value_import_instance = ImportPropertySelectValueInstance(data={"value": self.value},
                                                                import_process=self.import_process,
                                                                property=product_type_property)

    def pre_process_logic(self):

        # If the property is not provided, run the property import.
        if not self.product_type:
            self.property_select_value_import_instance.process()
            self.product_type = self.property_select_value_import_instance.instance

    def process_logic(self):
        fac = ProductPropertiesRuleImport(self, self.import_process, instance=self.instance)
        fac.run()

        self.instance = fac.instance

    def before_process_item_logic(self, item_import_instance):
        pass

    def after_process_item_logic(self, instance, remote_instance):
        pass

    def post_process_logic(self):

        if hasattr(self, 'items'):

            for item_data in self.items:
                item_import_instance = ImportProductPropertiesRuleItemInstance(data=item_data,
                                                                               import_process=self.import_process,
                                                                               rule=self.instance)
                self.before_process_item_logic(item_import_instance)
                item_import_instance.process()
                self.after_process_item_logic(item_import_instance.instance, item_import_instance.remote_instance)


class ImportProductPropertiesRuleItemInstance(AbstractImportInstance):
    """
    Import instance for ProductPropertiesRuleItem.

    Expected data keys:
      - type: The rule type (e.g., REQUIRED_IN_CONFIGURATOR, OPTIONAL_IN_CONFIGURATOR, REQUIRED, OPTIONAL).
      - sort_order: (Optional) The sort order for the rule item.

    Optionally, a 'rule' or a 'property' may be provided externally.
    """

    def __init__(self, data: dict, import_process=None, rule=None, property=None, instance=None):
        super().__init__(data, import_process, instance)
        self.rule = rule
        self.property = property

        # For 'type', default to ProductPropertiesRuleItem.OPTIONAL if not provided.
        self.set_field_if_exists('type', default_value=ProductPropertiesRuleItem.OPTIONAL)
        self.set_field_if_exists('sort_order')
        self.set_field_if_exists('rule_data')
        self.set_field_if_exists('property_data')

        if self.property is None:
            # we might want to add the property directly into data because most of the times the items will be created
            # in bulk
            self.set_field_if_exists('property')

        self.validate()

        # this will also do validation
        self._set_import_instances()

    @property
    def local_class(self):
        return ProductPropertiesRuleItem

    @property
    def updatable_fields(self):
        return ['sort_order', 'type']

    def validate(self):

        allowed_types = [rule[0] for rule in ProductPropertiesRuleItem.RULE_TYPES]
        if self.type not in allowed_types:
            raise ValueError(f"Invalid rule type: {self.type}. Allowed types are: {allowed_types}")

        if not (self.rule or (hasattr(self, 'rule_data') and self.rule_data)):
            raise ValueError("Either a 'rule' or 'rule_data' must be provided.")

        if not (self.property or (hasattr(self, 'property_data') and self.property_data)):
            raise ValueError("Either a 'property' or 'property_data' must be provided.")

    def _set_import_instances(self):

        if not self.property:
            self.property_import_instance = ImportPropertyInstance(self.property_data, self.import_process)

        if not self.rule:
            self.rule_import_instance = ImportProductPropertiesRuleInstance(self.rule_data, self.import_process)

    def pre_process_logic(self):

        # If the property is not provided, run the property import.
        if not self.property:
            self.property_import_instance.process()
            self.property = self.property_import_instance.instance

        if not self.rule:
            self.rule_import_instance.process()
            self.rule = self.rule_import_instance.instance

    def process_logic(self):
        fac = ProductPropertiesRuleItemImport(self, self.import_process, instance=self.instance)
        fac.run()

        self.instance = fac.instance


class GetSelectValueMixin:

    def get_select_value(self, value, property=None):

        if property is None:
            property = self.property

        property_value_import_instance = ImportPropertySelectValueInstance(data={"value": value},
                                                                     import_process=self.import_process,
                                                                     property=property)
        property_value_import_instance.set_language(self.language)
        property_value_import_instance.process()
        return property_value_import_instance.instance


class ImportProductPropertyInstance(AbstractImportInstance, GetSelectValueMixin):
    """
    Import instance for PropertySelectValue.

    # FIXME: This docstring is not clear. Maybe out of date?  Perhaps supply example.

    Expected data keys:
      - value: The select value to be imported.
      - property_data: (Optional) A dict for importing the Property if no property is provided.
      - product_data
      - translations

    Optionally, if the property already exists, the data may contain a 'property' key.
    """

    def __init__(self, data: dict, import_process=None, property=None, product=None, instance=None):
        super().__init__(data, import_process, instance)
        self.property = property
        self.product = product

        self.set_field_if_exists('value')
        self.set_field_if_exists('value_is_id', default_value=False)
        self.set_field_if_exists('property_data')
        self.set_field_if_exists('product_data')
        self.set_field_if_exists('translations')

        if self.property is None:
            # we might want to add the property directly into data because most of the times the product properties
            # will be created in bulk
            self.set_field_if_exists('property')

        self.validate()
        self._set_property_import_instance()
        self._set_product_import_instance()

        self.factory_class = ProductPropertyImport

    @property
    def local_class(self):
        return ProductProperty

    @property
    def local_translation_class(self):
        return ProductPropertyTextTranslation

    @property
    def updatable_fields(self):
        return ['value_boolean', 'value_int', 'value_float', 'value_date', 'value_datetime',
                'value_select', 'value_multi_select', 'value_text', 'value_description']

    def validate(self):
        """
        Validate that the 'value' key exists.
        """
        if not hasattr(self, 'value'):
            raise ValueError("The 'value' field is required.")

        if not getattr(self, 'property_data', None) and not self.property:
            raise ValueError("Either a 'property' or 'property_data' must be provided.")

        if not getattr(self, 'product_data', None) and not self.product:
            raise ValueError("Either a 'property' or 'property_data' must be provided.")

    def _set_property_import_instance(self):

        if not self.property and hasattr(self, 'property_data'):
            self.property_import_instance = ImportPropertyInstance(self.property_data, self.import_process)

    def _set_product_import_instance(self):
        from imports_exports.factories.products import ImportProductInstance

        if not self.product and hasattr(self, 'product_data'):
            self.product_import_instance = ImportProductInstance(self.product_data, self.import_process)

    def pre_process_logic(self):

        if not self.property:
            self.property_import_instance.process()
            self.property = self.property_import_instance.instance

        if not self.product:
            self.product_import_instance.process()
            self.product = self.product_import_instance.instance

        self.set_value()

        # we set this in case is a translations
        self.product_property = SimpleNamespace(property=self.property, product=self.product)
        self.set_factory_class()

    def set_factory_class(self):
        if self.property.type in Property.TYPES.TRANSLATED:
            self.factory_class = TranslatedProductPropertyImport
        else:
            self.factory_class = ProductPropertyImport

    def set_value(self):

        if self.property.type == Property.TYPES.INT:
            self.value_int = int(self.value)
        elif self.property.type == Property.TYPES.FLOAT:
            self.value_float = float(self.value)
        elif self.property.type == Property.TYPES.BOOLEAN:
            self.value_boolean = bool(self.value)
        elif self.property.type in [Property.TYPES.DATE, Property.TYPES.DATETIME]:

            date_format = '%Y-%m-%d %H:%M:%S'
            parsed_datetime = datetime.strptime(self.value, date_format)

            if self.property.type == Property.TYPES.DATETIME:
                self.value_datetime = parsed_datetime
            else:
                self.value_date = parsed_datetime.date()

        elif self.property.type == Property.TYPES.TEXT:
            self.value_text = self.value
        elif self.property.type == Property.TYPES.DESCRIPTION:
            self.value_description = self.value

        elif self.property.type == Property.TYPES.SELECT:

            if self.value_is_id:
                self.value_select = PropertySelectValue.objects.get(id=self.value)
            else:
                self.value_select = self.get_select_value(self.value)

        elif self.property.type == Property.TYPES.MULTISELECT:

            if self.value_is_id:
                ids = [int(x) for x in self.value]
                self.value_multi_select = PropertySelectValue.objects.filter(id__in=ids)
            else:

                if isinstance(self.value, str):
                    values = [x.strip() for x in self.value.split(',') if x.strip()]
                elif isinstance(self.value, list):
                    values = self.value
                else:
                    values = []

                ids = []
                for value in values:
                    ids.append(self.get_select_value(value).id)

                self.value_multi_select = PropertySelectValue.objects.filter(id__in=ids)

    def process_logic(self):
        fac = self.factory_class(self, self.import_process, instance=self.instance)
        fac.run()

        self.instance = fac.instance

        if (
            fac.created and
            self.factory_class == TranslatedProductPropertyImport and
            not (hasattr(self, 'translations') and len(self.translations) > 0)
        ):
            self.create_translation()

    def create_translation(self):

        self.translation = ProductPropertyTextTranslation.objects.create(
            multi_tenant_company=self.instance.multi_tenant_company,
            product_property=self.instance,
            language=self.language,
            value_text=getattr(self, 'value_text', None),
            value_description=getattr(self, 'value_description', None)
        )

    def post_process_logic(self):

        if not hasattr(self, 'translations'):
            return

        if self.property.type not in Property.TYPES.TRANSLATED:
            return

        for translation in getattr(self, 'translations', []):
            language = translation.get('language')
            value = translation.get('value')

            if not language or not value:
                continue

            value_field = 'value_text' if self.property.type == Property.TYPES.TEXT else 'value_description'
            translation_obj, _ = ProductPropertyTextTranslation.objects.get_or_create(
                multi_tenant_company=self.instance.multi_tenant_company,
                product_property=self.instance,
                language=language,
            )

            if getattr(translation_obj, value_field) != value:
                setattr(translation_obj, value_field, value)
                translation_obj.save()
