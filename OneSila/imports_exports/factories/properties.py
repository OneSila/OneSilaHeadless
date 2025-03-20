import abc

from imports_exports.factories.mixins import ImportOperationMixin, AbstractImportInstance
from llm.factories.property_type_detector import DetectPropertyTypeLLM
from properties.models import Property, PropertyTranslation


class ImportUsingInternalName(ImportOperationMixin):
    local_class = Property
    local_translation_class = PropertyTranslation
    get_identifiers = ['internal_name', 'type']


class ImportUsingTranslationName(ImportOperationMixin):
    local_class = Property
    local_translation_class = PropertyTranslation
    get_using_translation = True
    translation_get_value = 'property'
    get_identifiers = ['name', 'property__type']


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

    def __init__(self, data: dict, multi_tenant_company=None):
        super().__init__(data, multi_tenant_company)

        # Set defaults for optional boolean fields
        self.data.setdefault('is_public_information', True)
        self.data.setdefault('add_to_filters', True)
        self.data.setdefault('has_image', False)

        # First, validate required keys and boolean field types (ignoring 'type').
        self.validate()

        # If 'type' is missing or empty, detect it.
        if not self.data.get('type'):
            self.data['type'] = self.detect_type()

        # Now validate that the property type is one of the allowed types.
        self.validate_type()

    @abc.abstractmethod
    def detect_type(self):
        """
        Detects and returns the property type if not provided.
        Concrete implementations must override this method.
        """
        llm = DetectPropertyTypeLLM(self.data, self.multi_tenant_company)
        self.data['type'] = llm.detect_type()

    def validate(self):
        """
        Validates that at least one of 'internal_name' or 'name' is provided
        and that the boolean fields have boolean values.
        """
        if not (self.data.get('internal_name') or self.data.get('name')):
            raise ValueError("Either 'internal_name' or 'name' must be provided.")
        for key in ['is_public_information', 'add_to_filters', 'is_product_type', 'has_image']:
            if not isinstance(self.data.get(key), bool):
                raise ValueError(f"Field '{key}' must be a boolean value.")

    def validate_type(self):
        """
        Validates that the property type is one of the allowed types.
        """
        prop_type = self.data.get('type')
        if prop_type not in self.ALLOWED_TYPES:
            raise ValueError(
                f"Invalid property type: {prop_type}. Allowed types are: {self.ALLOWED_TYPES}"
            )

    def process(self, import_instance):
        """
        Processes the validated import data.

        This method chooses which factory to use based on the provided identifiers:
          - If 'internal_name' is present in the data, use ImportUsingInternalName.
          - Otherwise, use ImportUsingTranslationName.

        :param import_instance: The import instance (e.g., a SaleChannelImport instance) is mandatory.

        The method then passes the import instance and this instance (as structured data)
        to the chosen factory, assigns optional mirror and sales channel configuration if provided,
        calls run(), and finally stores the created/updated instance in self.instance.
        """
        # Decide which factory to use based on the data.
        if self.data.get('internal_name'):
            factory_class = ImportUsingInternalName
        else:
            factory_class = ImportUsingTranslationName

        # Instantiate the factory, providing the mandatory import_instance.
        fac = factory_class(import_instance, self)

        # Pass optional configurations if provided.
        if self.mirror_model_class is not None:
            fac.mirror_model_class = self.mirror_model_class
        if self.mirror_model_map:
            fac.mirror_model_map = self.mirror_model_map
        if self.sales_channel_class is not None:
            fac.sales_channel_class = self.sales_channel_class
        if self.sales_channel_id is not None:
            fac.sales_channel_id = self.sales_channel_id

        # Run the factory to process the import.
        fac.run()

        # Save the created/updated instance.
        self.instance = fac.instance

    def process_additional(self):
        pass
