import logging

from django.db.models.fields.related import ManyToManyField
from core.helpers import get_nested_attr
from django.conf import settings
import abc

logger = logging.getLogger(__name__)


class AbstractImportInstance(abc.ABC):
    """
    Abstract base class for any import instance that processes a data dict.

    This class provides a common framework that:
      - Initializes with a data dictionary.
      - Sets default optional configuration attributes:
            mirror_model_class, mirror_model_map, mirror_model_defaults
            sales_channel_class, sales_channel_id.
      - Forces validation immediately after initialization.
      - Requires concrete implementations to implement validate() and process(import_instance).
    """

    def __init__(self, data: dict, import_process=None, instance=None):
        self.import_process = import_process
        self.instance = instance
        self.multi_tenant_company = import_process.multi_tenant_company if import_process else None
        self.data = data.copy()

        self.mirror_model_class = None
        self.mirror_model_map = {}
        self.mirror_model_defaults = {}
        self.sales_channel = None
        self.remote_instance = None

        if 'language' in data:
            self.language = data['language']
        else:
            if self.multi_tenant_company:
                self.language = self.multi_tenant_company.language
            else:
                self.language = settings.LANGUAGE_CODE

    @property
    def local_class(self):
        raise NotImplementedError("Needs to be added in the subclass.")

    @property
    def local_translation_class(self):
        return None

    @property
    def updatable_fields(self):
        return []

    def set_language(self, language):
        self.language = language

    def prepare_mirror_model_class(self, mirror_model_class, sales_channel, mirror_model_map, mirror_model_defaults=None):
        self.sales_channel = sales_channel
        self.mirror_model_class = mirror_model_class
        self.mirror_model_map = mirror_model_map

        if mirror_model_defaults:
            self.mirror_model_defaults = mirror_model_defaults

    def set_field_if_exists(self, field: str, default_value=None):

        if field in self.data:
            setattr(self, field, self.data.get(field))
            return

        if default_value is not None:
            setattr(self, field, default_value)

    @abc.abstractmethod
    def validate(self):
        """
        Validate the data dictionary.
        Concrete implementations must override this method.
        """
        pass

    @abc.abstractmethod
    def process_logic(self):
        pass

    def pre_process_logic(self):
        pass

    def post_process_logic(self):
        pass

    def set_remote_instance(self, remote_instance):
        self.remote_instance = remote_instance

    def process(self):
        """
        Process the validated import data.

        :param import_process: The import instance (e.g., a SaleChannelImport instance) is mandatory.
        Concrete implementations must override this method.
        """

        if self.import_process is None:
            raise ValueError("Import instance must be provided.")

        self.pre_process_logic()
        self.process_logic()
        self.post_process_logic()

    def __repr__(self):
        return f"<{self.__class__.__name__} data={self.data}>"


class ImportOperationMixin:
    """
    Mixin for import operations that handles retrieving or creating the local instance,
    updating its fields based on the structured data, and (optionally) creating mirror data
    for a sales channel.

    Configuration attributes (to be set in subclasses):
      - get_identifiers: List of field names (or nested paths) used to filter the local instance
    """
    get_identifiers = []  # e.g. ['sku'] or ['nested__identifier']
    get_translation_identifiers = []
    get_using_translation = False
    translation_get_value = None
    allow_edit = True  # for some imports we don't have what to edit
    allow_translation_edit = False

    def __init__(self, import_instance, import_process, instance=None):
        """
        :param import_process: The import model instance (which must have a multi_tenant_company attribute)
        :param import_instance: The processed data (currently a dict) used for the import
        """
        self.import_process = import_process
        self.import_instance = import_instance
        self.multi_tenant_company = import_process.multi_tenant_company
        self.instance = instance

        # This will hold the local instance (e.g., Property) once retrieved or created.
        self.created = False

        self.get_kwargs = {}
        self.get_translation_kwargs = {}

        # useful when we don't find the translation but our identifier without the translation is too generic
        # ex when getting property by the translation if is not existing if we don't force create we will try to do get_or_create by type only
        self.force_created = False

    def build_kwargs(self):
        """
        Build kwargs for filtering the local_class using get_identifiers.
        Always adds multi_tenant_company.
        """
        def build_kwargs(identifiers):
            kwargs = {'multi_tenant_company': self.multi_tenant_company}
            for identifier in identifiers:
                value = get_nested_attr(self.import_instance, identifier)
                if value is not None:
                    kwargs[identifier] = value

            return kwargs

        self.get_kwargs = build_kwargs(self.get_identifiers)
        self.get_translation_kwargs = build_kwargs(self.get_translation_identifiers)

    def get_translation(self):
        """
        If get_using_translation is True, attempt to find the local instance using the translation model.
        This filters local_translation_class using the same get_identifiers.
        """

        if self.import_instance.local_translation_class:
            self.translation_obj = self.import_instance.local_translation_class.objects.filter(**self.get_translation_kwargs).first()
            if self.translation_obj and self.translation_get_value:
                # Assuming the translation object has an attribute (or FK) that points to the local instance.
                self.instance = getattr(self.translation_obj, self.translation_get_value, None)
                logger.debug(f"Found local instance via translation: {self.instance}")

            else:
                self.force_created = True

    def get_or_create_instance(self):
        """
        Attempts to retrieve the local instance using the built kwargs; if not found, create it.
        """
        if not self.instance:

            if self.force_created:
                self.instance = self.import_instance.local_class.objects.create(**self.get_kwargs)
                self.created = True
            else:
                self.instance, self.created = self.import_instance.local_class.objects.get_or_create(**self.get_kwargs)

        return self.instance

    def update_instance(self):
        """
        Update fields on the local instance with values from import_instance.
        Only changes fields if the new value is different.
        """
        to_save = False
        for key in self.import_instance.updatable_fields:
            if not hasattr(self.import_instance, key):
                continue

            val = getattr(self.import_instance, key)
            field = self.instance._meta.get_field(key)

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

    def update_translation_instance(self):
        """
        Update fields on the translation object (if available) with values from import_instance.
        """
        if not getattr(self, "translation_obj", None):
            return

        to_save = False
        for key in self.import_instance.updatable_fields:
            if not hasattr(self.import_instance, key):
                continue

            val = getattr(self.import_instance, key)
            current_val = getattr(self.translation_obj, key, None)

            if current_val != val:
                setattr(self.translation_obj, key, val)
                to_save = True
                logger.debug(f"Updated translation field '{key}': {current_val} -> {val}")

        if to_save:
            self.translation_obj.save()
            logger.info(f"Translation instance updated: {self.translation_obj}")

    def _get_or_create_mirror_data(self):
        """
        Creates (or retrieves) a mirror model instance that links the local instance
        to a specific sales channel integration.

        This method relies on the following attributes defined on the import_instance:
          - `mirror_model_class`: The mirror model class to be used (e.g. MagentoProduct).
          - `mirror_model_map`: A dictionary mapping mirror model fields to values.
            Supported value types:
              - `"*"`: Use the full `self.instance` object.
              - String: Treated as an attribute name to fetch from `self.instance`.

          - `mirror_model_defaults` (optional): A dictionary of literal values to override or extend
            the generated `mirror_data`. Useful for fields like `remote_sku` or constant values.

        Example:
            import_instance.prepare_mirror_model_class(
                MagentoProduct,
                sales_channel,
                {
                    "local_instance": "*",
                    "product_type": "type",
                },
                mirror_model_defaults={
                    "remote_sku": "ABC123"
                }
            )

        Returns:
            The created or retrieved mirror instance, or None if no mirror model is configured.
        """
        if self.import_instance.mirror_model_class and self.import_instance.mirror_model_map:
            mirror_data = {
                'sales_channel': self.import_instance.sales_channel,
                'multi_tenant_company': self.import_instance.multi_tenant_company,
            }

            for mirror_field, local_field in self.import_instance.mirror_model_map.items():
                if local_field == "*":
                    mirror_data[mirror_field] = self.instance
                elif isinstance(local_field, str):
                    mirror_data[mirror_field] = getattr(self.instance, local_field, None)

            if hasattr(self.import_instance, 'mirror_model_defaults'):
                mirror_data.update(self.import_instance.mirror_model_defaults)

            self.mirror_instance, _ = self.import_instance.mirror_model_class.objects.get_or_create(**mirror_data)
            logger.info(f"Created mirror instance: {self.mirror_instance}")
            self.import_instance.set_remote_instance(self.mirror_instance)

            return self.mirror_instance

        return None

    def _create_mirror_data_needed(self):
        return self.import_instance.mirror_model_class and self.import_instance.sales_channel

    def run(self):
        """
        Orchestrates the import operation:
          1. Optionally try to get the local instance using translation.
          2. If not found, perform get_or_create on the local model.
          3. Update the local instance with the structured data.
          4. Optionally create mirror data for a sales channel.
        """
        if self.instance is None:

            self.build_kwargs()
            if self.get_using_translation:
                self.get_translation()

            self.get_or_create_instance()

        if self.allow_edit:
            self.update_instance()

        if self.allow_translation_edit:
            self.update_translation_instance()

        if self._create_mirror_data_needed():
            self._get_or_create_mirror_data()
