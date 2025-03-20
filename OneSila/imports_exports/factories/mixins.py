import logging
from django.db import IntegrityError
from core.helpers import get_nested_attr
import abc

logger = logging.getLogger(__name__)


class AbstractImportInstance(abc.ABC):
    """
    Abstract base class for any import instance that processes a data dict.

    This class provides a common framework that:
      - Initializes with a data dictionary.
      - Sets default optional configuration attributes:
            mirror_model_class, mirror_model_map,
            sales_channel_class, sales_channel_id.
      - Forces validation immediately after initialization.
      - Requires concrete implementations to implement validate() and process(import_instance).
    """

    def __init__(self, data: dict, multi_tenant_company=None):
        self.initial_data = data
        self.multi_tenant_company = multi_tenant_company
        self.data = data.copy()

        self.instance = None
        self.mirror_model_class = None
        self.mirror_model_map = {}
        self.sales_channel_class = None
        self.sales_channel_id = None


    @abc.abstractmethod
    def validate(self):
        """
        Validate the data dictionary.
        Concrete implementations must override this method.
        """
        pass

    @abc.abstractmethod
    def process(self, import_instance):
        """
        Process the validated import data.

        :param import_instance: The import instance (e.g., a SaleChannelImport instance) is mandatory.
        Concrete implementations must override this method.
        """
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} data={self.data}>"


class ImportOperationMixin:
    """
    Mixin for import operations that handles retrieving or creating the local instance,
    updating its fields based on the structured data, and (optionally) creating mirror data
    for a sales channel.

    Configuration attributes (to be set in subclasses):
      - local_class: The Django model to be created/updated (e.g. Property)
      - local_translation_class: Optional translation model for alternative lookup
      - get_identifiers: List of field names (or nested paths) used to filter the local instance
      - get_using_translation: Boolean; if True, use the translation model to get the local instance
      - translation_get_value: Field name on the translation object that points to the local instance
      - mirror_model_class: (Optional) Mirror model class to be created (e.g. RemoteProperty)
      - mirror_model_map: Dict mapping mirror model fields to local instance field names
      - sales_channel_class: (Optional) Sales channel model class (e.g. MagentoSalesChannel)
      - sales_channel_id: (Optional) ID to look up the sales channel instance
    """
    local_class = None
    local_translation_class = None
    get_identifiers = []  # e.g. ['sku'] or ['nested__identifier']
    get_using_translation = False
    translation_get_value = None

    mirror_model_class = None
    mirror_model_map = {}  # e.g. {'remote_field': 'local_field'}
    sales_channel_class = None
    sales_channel_id = None

    def __init__(self, import_instance, structured_data):
        """
        :param import_instance: The import model instance (which must have a multi_tenant_company attribute)
        :param structured_data: The processed data (currently a dict) used for the import
        """
        self.import_instance = import_instance
        self.structured_data = structured_data
        self.multi_tenant_company = import_instance.multi_tenant_company

        # This will hold the local instance (e.g., Property) once retrieved or created.
        self.instance = None
        self.get_kwargs = {}

    def build_get_kwargs(self):
        """
        Build kwargs for filtering the local_class using get_identifiers.
        Always adds multi_tenant_company.
        """
        kwargs = {'multi_tenant_company': self.multi_tenant_company}
        for identifier in self.get_identifiers:
            value = get_nested_attr(self.structured_data, identifier)
            if value is not None:
                kwargs[identifier] = value

        logger.debug(f"Built get kwargs: {kwargs}")
        self.get_kwargs = kwargs

    def get_translation(self):
        """
        If get_using_translation is True, attempt to find the local instance using the translation model.
        This filters local_translation_class using the same get_identifiers.
        """
        if self.local_translation_class:
            translation_obj = self.local_translation_class.objects.filter(**self.get_kwargs()).first()
            if translation_obj and self.translation_get_value:
                # Assuming the translation object has an attribute (or FK) that points to the local instance.
                self.instance = getattr(translation_obj, self.translation_get_value, None)
                logger.debug(f"Found local instance via translation: {self.instance}")

        return self.instance

    def get_or_create_instance(self):
        """
        Attempts to retrieve the local instance using the built kwargs; if not found, create it.
        """
        if not self.instance:
            kwargs = self.build_get_kwargs()
            self.instance, created = self.local_class.objects.get_or_create(**kwargs)
            if created:
                logger.info(f"Created new local instance: {self.instance}")
            else:
                logger.info(f"Found existing local instance: {self.instance}")
        return self.instance

    def update_instance(self):
        """
        Update fields on the local instance with values from structured_data.
        Only changes fields if the new value is different.
        """
        to_save = False
        for key, val in self.structured_data.items():
            current_val = getattr(self.instance, key, None)
            if current_val != val:
                setattr(self.instance, key, val)
                to_save = True
                logger.debug(f"Updated field '{key}': {current_val} -> {val}")
        if to_save:
            self.instance.save()
            logger.info(f"Local instance updated: {self.instance}")

    def _create_mirror_data(self):
        """
        Creates a mirror model instance using mirror_model_map and the local instance.
        Optionally associates it with a sales channel if configured.
        """
        if self.mirror_model_class and self.mirror_model_map:
            mirror_data = {}
            for mirror_field, local_field in self.mirror_model_map.items():
                mirror_data[mirror_field] = getattr(self.instance, local_field, None)
            if self.sales_channel_class and self.sales_channel_id:
                try:
                    sales_channel = self.sales_channel_class.objects.get(id=self.sales_channel_id)
                    mirror_data['sales_channel'] = sales_channel
                except self.sales_channel_class.DoesNotExist:
                    logger.error("Sales channel not found for mirror creation.")
            mirror_instance = self.mirror_model_class.objects.create(**mirror_data)
            logger.info(f"Created mirror instance: {mirror_instance}")
            return mirror_instance
        return None

    def _create_mirror_data_needed(self):
        return self.sales_channel_class and self.sales_channel_id and self.mirror_model_class

    def run(self):
        """
        Orchestrates the import operation:
          1. Optionally try to get the local instance using translation.
          2. If not found, perform get_or_create on the local model.
          3. Update the local instance with the structured data.
          4. Optionally create mirror data for a sales channel.
        """
        self.build_get_kwargs()
        if self.get_using_translation:
            self.get_translation()

        self.get_or_create_instance()
        self.update_instance()

        if self._create_mirror_data_needed():
            self._create_mirror_data()
