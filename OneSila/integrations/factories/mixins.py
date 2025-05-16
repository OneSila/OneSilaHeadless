import traceback
import inspect
import sys

from django.db import IntegrityError

from core.helpers import get_nested_attr, clean_json_data
from ..signals import remote_instance_pre_create, remote_instance_post_create, remote_instance_post_update, remote_instance_pre_update, \
    remote_instance_pre_delete, remote_instance_post_delete
from ..models import IntegrationLog
import logging

logger = logging.getLogger(__name__)


class IntegrationInstanceOperationMixin:
    """
    Mixin providing common operations for remote instance factories.
    Includes methods for API interaction, response handling, logging, and error management.
    """
    integration_key = 'integration'  # the name of the main integration key ex sales_channel / remote_account

    def get_api(self):
        """
        Retrieves the API client or wrapper based on the sales channel.
        This method should be overridden to return the appropriate API client.
        """
        raise NotImplementedError("Subclasses must implement the get_api method to return the API client.")

    def set_api(self):
        if not hasattr(self, 'api') or self.api is None:
            self.api = self.get_api()

    def serialize_response(self, response):
        """
        Serializes the response from the remote API.
        """
        return response.json()

    def get_identifiers(self, fixing_caller='run'):
        """
        Generates a log identifier to reflect the current class and calling method context.
        """
        frame = inspect.currentframe()
        caller = frame.f_back.f_code.co_name
        class_name = self.__class__.__name__

        fixing_class = getattr(self, 'fixing_identifier_class', None)
        fixing_identifier = None
        if fixing_caller and fixing_class:
            fixing_identifier = f"{fixing_class.__name__}:{fixing_caller}"

        return f"{class_name}:{caller}", fixing_identifier

    def log_action_for_instance(self, remote_instance, action, response_data, payload, identifier):
        if not remote_instance:
            raise ValueError("A valid remote_instance must be provided for logging.")

        remote_instance.add_log(
            action=action,
            response=response_data,
            payload=payload,
            identifier=identifier,
            remote_product=getattr(self, 'remote_product', None)
        )

    def log_action(self, action, response_data, payload, identifier):
        """
        Logs actions for remote instance operations.
        """
        self.remote_instance.add_log(
            action=action,
            response=response_data,
            payload=payload,
            identifier=identifier,
            remote_product=getattr(self, 'remote_product', None)
        )

    def log_error(self, exception, action, identifier, payload, fixing_identifier=None):
        """
        Logs errors for user exceptions or admin exceptions depending on the exception type.
        """
        tb = traceback.format_exc()
        error_message = str(exception)
        payload = clean_json_data(payload)

        if hasattr(self.integration._meta, 'user_exceptions') and isinstance(exception, self.integration._meta.user_exceptions):
            self.remote_instance.add_user_error(
                action=action,
                response=error_message,
                payload=payload,
                error_traceback=tb,
                identifier=identifier,
                remote_product=getattr(self, 'remote_product', None),
                fixing_identifier=fixing_identifier
            )
        else:
            self.remote_instance.add_admin_error(
                action=action,
                response=error_message,
                payload=payload,
                error_traceback=tb,
                identifier=identifier,
                remote_product=getattr(self, 'remote_product', None),
                fixing_identifier=fixing_identifier
            )

    def customize_payload(self):
        """
        Override this method to add customizations to the payload.
        """
        return self.payload

    def get_mapped_field(self, data, map_path, is_model=False):
        """
        Retrieves a nested field from a dictionary or model based on the map path.
        Supports nested fields using '__' notation.

        :param data: The data source, either a dictionary or model instance.
        :param map_path: A string representing the field path, e.g., 'field1__field2'.
        :param is_model: Boolean flag indicating whether the data source is a model.
        :return: The retrieved value or None if not found.
        """
        fields = map_path.split('__')
        result = data

        for field in fields:
            if is_model:
                result = getattr(result, field, None)
            else:
                result = result.get(field, None)
            if result is None:
                break

        return result

    def _determine_remote_product(self, kwargs):
        """
        Determines the remote product based on the following logic:
        1. Check if 'remote_product' is in kwargs.
           - If not, return None.
        2. If 'remote_product' is in kwargs and is None, try to get it from remote_instance.
        3. If 'remote_product' is in kwargs and is not None, return it.
        4. If 'remote_product' is None in kwargs and remote_instance doesn't have it, use get_remote_product.
        """
        if 'remote_product' not in kwargs:
            return None

        remote_product = kwargs.get('remote_product')

        if remote_product is None:
            if self.remote_instance and isinstance(self.remote_instance, self.remote_model_class) and hasattr(self.remote_instance, 'remote_product'):
                return self.remote_instance.remote_product
            else:
                return self.get_remote_product(self.get_mapped_field(self, self.local_product_map, is_model=True))

        return remote_product

    def get_remote_product(self, product):
        """
        Placeholder method to be implemented in subclasses if specific behavior is required.
        """
        raise NotImplementedError("Subclasses should implement this method to get the remote product.")

    def post_action_payload_modify(self):
        """
        A method where we can modify the payload after is used so it is saved with new data used to then be compared
        in needs update
        """
        pass


class IntegrationInstanceCreateFactory(IntegrationInstanceOperationMixin):
    local_model_class = None  # The Sila Model
    remote_model_class = None  # The Mirror Model
    remote_id_map = 'id'  # Default remote ID mapping to get the remote id from the response
    field_mapping = {}  # Mapping of local fields to remote fields, should be overridden in subclasses
    default_field_mapping = {}  # Mapping of default values on create

    # Configurable API details
    api_package_name = None  # The package name (e.g., 'properties')
    api_method_name = 'create'  # The method name (e.g., 'create')

    # If something we try to create already exists on the remote server we del with the following configs
    enable_fetch_and_update = False  # If True, check for duplicate remote instance, fetch it, and trigger an update flow
    already_exists_exception = None  # Set to a custom exception type if applicable, or None
    update_factory_class = None  # Update factory to use if remote already exists
    update_if_not_exists = False  # Whether to trigger an update flow if the remote instance is already present

    def __init__(self, integration, local_instance=None, api=None):
        self.local_instance = local_instance  # Instance of the local model
        self.integration = integration  # Sales channel associated with the sync
        self.successfully_created = True  # Tracks if creation was successful
        self.payload = {}  # Will hold the payload data
        self.remote_instance_data = {}  # Will hold data for initializing the remote instance
        self.api = api

        setattr(self, self.integration_key, self.integration.get_real_instance())

    def preflight_check(self):
        """
        Perform preliminary checks  before proceeding with any operation.
        This method should be overridden in subclasses if specific checks are needed.
        """
        return True

    def preflight_process(self):
        """
        Perform preliminary checks or actions before proceeding with any operation.
        This method should be overridden in subclasses if specific checks are needed.
        """
        pass

    def build_payload(self):
        """
        Constructs the payload for the remote instance using the field mapping provided,
        supporting nested fields in the local instance using '__' notation.
        """
        self.payload = {}
        for local_field, remote_field in self.field_mapping.items():
            # Use the helper function to handle nested field lookups
            self.payload[remote_field] = get_nested_attr(self.local_instance, local_field)

        if hasattr(self, 'default_field_mapping') and self.default_field_mapping:
            # Merge the default field mapping into the payload.
            # Values in the payload (from field_mapping) will override those in default_field_mapping.
            self.payload = {**self.default_field_mapping, **self.payload}

        return self.payload

    def build_remote_instance_data(self):
        """
        Constructs the data for initializing the remote instance, using local_instance.
        """
        self.remote_instance_data = {'local_instance': self.local_instance, self.integration_key: self.integration}
        return self.remote_instance_data

    def customize_remote_instance_data(self):
        """
        Override this method to customize the data for initializing the remote instance.
        """
        return self.remote_instance_data

    def initialize_remote_instance(self):
        """
        Initialize the remote instance based on the remote instance data & save so we can add logs to it
        """
        self.remote_instance_data['multi_tenant_company'] = self.integration.multi_tenant_company
        self.remote_instance = self.remote_model_class(**self.remote_instance_data)
        remote_instance_pre_create.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

        try:
            self.remote_instance.save()
        except IntegrityError:

            if not self.enable_fetch_and_update:
                raise

            self.remote_instance = self.remote_model_class.objects.get(**self.remote_instance_data)

        logger.debug(f"Initialized remote instance: {self.remote_instance}")

    def modify_remote_instance(self, response_data):
        """
        Override this method to modify the remote instance before saving.
        """
        pass

    def set_remote_id(self, response_data):
        """
        Sets the remote ID based on the response data using the mapping provided.
        """
        # Retrieve remote_id using the get_mapped_field utility function
        self.remote_instance.remote_id = self.get_mapped_field(response_data, self.remote_id_map)

    def create_remote(self):
        """
        Implements the remote creation logic using the API client.
        This method creates the actual remote object on the external system.
        """
        # Retrieve the API package (e.g., 'properties')
        api_package = getattr(self.api, self.api_package_name, None)
        if not api_package:
            raise ValueError(f"API package '{self.api_package_name}' not found in the API client.")

        # Retrieve the API method (e.g., 'create')
        api_method = getattr(api_package, self.api_method_name, None)
        if not api_method:
            raise ValueError(f"API method '{self.api_method_name}' not found in the API package '{self.api_package_name}'.")

        # Call the API method with the payload
        return api_method(**self.payload)

    def post_create_process(self):
        """
        Override this method to add logic after create when we don't want to decentralize with signals
        """
        pass

    def is_duplicate_error(self, error):
        """
        Override this method to implement custom logic to decide if the error indicates that
        the remote object already exists (e.g., by checking the error message contents).
        By default, return False.
        """
        return False

    def fetch_existing_remote_data(self):
        """
        Override this method if enable_fetch_and_update is True.
        It should fetch and return the remote API response corresponding to the existing remote object.
        """
        raise NotImplementedError("Subclasses must override fetch_existing_remote_data() if enable_fetch_and_update is True.")

    def serialize_fetched_response(self, response):
        """
        Override this method to customize the serialization of a fetched remote response.
        By default, returns the same as serialize_response().
        """
        return self.serialize_response(response)

    def get_update_factory_class(self):
        """
        Check if update_factory_class is a class or a string.
        If it's a class, return it directly.
        If it's a string, import it dynamically.
        """
        if isinstance(self.update_factory_class, property):
            # If it's a property, call the getter method
            return self.update_factory_class.__get__(self, type(self))
        elif isinstance(self.update_factory_class, type):
            # If it's already a class, return it
            return self.update_factory_class
        elif isinstance(self.update_factory_class, str):
            # If it's a string, import it dynamically
            # Handle case where update_factory_class is in the same file
            # or is a relative import without full path
            if '.' not in self.update_factory_class:
                # Try to get the class from the current module
                current_module = sys.modules[self.__class__.__module__]
                if hasattr(current_module, self.update_factory_class):
                    return getattr(current_module, self.update_factory_class)

            # If not in current module, we'll fall through to the standard import
            module_path, class_name = self.update_factory_class.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        else:
            # Default case
            return self.update_factory_class

    def upload_flow(self):
        """
        Flow to trigger the update factory. This can be overrided
        """
        update_factory_class = self.get_update_factory_class()
        update_factory = update_factory_class(self.integration,
           self.local_instance,
           api=self.api,
           remote_instance=self.remote_instance)
        update_factory.run()

    def create(self):
        """
        Main method to orchestrate the creation process, including error handling and logging.
        """
        log_identifier, fixing_identifier = self.get_identifiers()

        try:
            logger.debug(f"Creating remote instance with payload: {self.payload}")
            require_update = False

            try:
                # Attempt to create the remote instance
                response = self.create_remote()
                response_data = self.serialize_response(response)
            except Exception as e:
                # First, if enable_fetch_and_update is enabled, check for duplicate error conditions
                if self.enable_fetch_and_update and ((self.already_exists_exception and isinstance(e, self.already_exists_exception)) or self.is_duplicate_error(e)):
                    logger.debug("Remote instance already exists; fetching existing remote data.")
                    response = self.fetch_existing_remote_data()

                    # Use a dedicated serialization method for fetched data
                    response_data = self.serialize_fetched_response(response)
                    require_update = True
                else:
                    raise e

            self.set_remote_id(response_data)
            self.modify_remote_instance(response_data)

            self.post_action_payload_modify()

            # Log the successful creation
            self.log_action(IntegrationLog.ACTION_CREATE, response_data, self.payload, log_identifier)

            # Send post-create signal
            remote_instance_post_create.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

            self.post_create_process()

        except Exception as e:
            self.successfully_created = False
            self.log_error(e, IntegrationLog.ACTION_CREATE, log_identifier, self.payload)

            raise

        finally:
            self.remote_instance.successfully_created = self.successfully_created
            self.remote_instance.save()
            logger.debug(f"Finished create process with success status: {self.successfully_created}")

        # After creation, if configured to trigger an update flow for an existing instance,
        # do so only if successfully_created is True.
        if self.enable_fetch_and_update and self.update_if_not_exists and self.update_factory_class and self.successfully_created and require_update:
            logger.debug("Remote instance existed; triggering update flow.")
            self.upload_flow()

    def run(self):

        if not self.preflight_check():
            return

        self.set_api()
        self.preflight_process()
        self.build_payload()
        self.customize_payload()
        self.build_remote_instance_data()
        self.customize_remote_instance_data()
        self.initialize_remote_instance()
        self.create()


class IntegrationInstanceUpdateFactory(IntegrationInstanceOperationMixin):
    local_model_class = None  # The Sila Model
    remote_model_class = None  # The Mirror Model
    field_mapping = {}  # Mapping of local fields to remote fields, should be overridden in subclasses
    updatable_fields = []  # Fields that are allowed to be updated
    local_product_map = 'local_instance__product'  # the way we go to the local product from the current instance (if possible)

    # Configurable API details
    api_package_name = None  # The package name (e.g., 'properties')
    api_method_name = 'update'  # The method name (e.g., 'update')

    # Configurable Create Factory for recreating instances if needed
    create_factory_class = None  # Should be overridden in subclasses with the specific Create Factory
    create_if_not_exists = False  # Configurable parameter to create the instance if not found

    def __init__(self, integration, local_instance=None, api=None, remote_instance=None, **kwargs):
        self.local_instance = local_instance  # Instance of the local model
        self.integration = integration  # Sales channel associated with the sync
        self.successfully_updated = True  # Tracks if update was successful
        self.payload = {}  # Will hold the payload data
        self.api = api

        setattr(self, self.integration_key, self.integration.get_real_instance())

        # we can give both the remote_instance as an id (from tasks) or the real instance
        if isinstance(remote_instance, self.remote_model_class):
            self.remote_instance = remote_instance
            self.remote_instance_id = remote_instance.id
        else:
            self.remote_instance = None
            self.remote_instance_id = remote_instance
            self.get_remote_instance()

        self.remote_product = self._determine_remote_product(kwargs)

    def preflight_check(self):
        """
        Perform preliminary checks  before proceeding with any operation.
        This method should be overridden in subclasses if specific checks are needed.
        """
        return True

    def preflight_process(self):
        """
        Perform preliminary actions before proceeding with any operation.
        This method should be overridden in subclasses if specific checks are needed.
        """
        pass

    def get_remote_instance(self):
        """
        Retrieve the remote instance based on the local instance and sales channel.
        Does not handle creation or deletion logic.
        """
        try:
            if self.remote_instance is None:
                if self.remote_instance_id is not None:
                    self.remote_instance = self.remote_model_class.objects.get(id=self.remote_instance_id)
                else:
                    get_payload = {
                        'local_instance': self.local_instance,
                        self.integration_key: self.integration
                    }
                    self.remote_instance = self.remote_model_class.objects.get(**get_payload)

            logger.debug(f"Fetched remote instance: {self.remote_instance}")
        except self.remote_model_class.DoesNotExist:
            self.remote_instance = None

    def handle_remote_instance_creation(self):
        """
        Handles the logic for recreating a remote instance if it wasn't created successfully.
        This method should be called after preflight processes, where the instance might need to be created.
        """
        if self.remote_instance is None:
            if self.create_if_not_exists:
                self.create_remote_instance()
                self.successfully_updated = False
            else:
                raise ValueError(f"Integration instance for value {self.local_instance} does not exist on website {self.integration} and cannot be updated.")
        elif not self.remote_instance.successfully_created:
            logger.debug(f"Integration instance not found, attempting to create for {self.local_instance}")
            self.remote_instance.delete()
            self.create_remote_instance()
            self.successfully_updated = False

    def create_remote_instance(self):
        """
        Attempts to recreate the remote instance using the specified Create Factory.
        """
        if not self.create_factory_class:
            raise ValueError("Create factory class must be specified to recreate remote instances.")

        create_factory = self.create_factory_class(self.integration, self.local_instance)
        create_factory.run()

        self.remote_instance = create_factory.remote_instance

    def build_payload(self):
        """
        Constructs the payload for the remote instance using the field mapping provided.
        If `updatable_fields` is specified, only include those fields; otherwise, include all fields from the mapping.
        Supports nested fields using '__' notation.
        """
        if hasattr(self, 'updatable_fields') and self.updatable_fields:
            # Only include fields specified in updatable_fields if provided
            self.payload = {
                remote_field: get_nested_attr(self.local_instance, local_field)
                for local_field, remote_field in self.field_mapping.items()
                if local_field in self.updatable_fields
            }
        else:
            # Include all fields from the field mapping if updatable_fields is not specified
            self.payload = {
                remote_field: get_nested_attr(self.local_instance, local_field)
                for local_field, remote_field in self.field_mapping.items()
            }
        return self.payload

    def update_remote(self):
        """
        Implements the remote update logic using the API client.
        This method updates the actual remote object on the external system.
        """
        # Retrieve the API package (e.g., 'properties')
        api_package = getattr(self.api, self.api_package_name, None)
        if not api_package:
            raise ValueError(f"API package '{self.api_package_name}' not found in the API client.")

        # Retrieve the API method (e.g., 'update')
        api_method = getattr(api_package, self.api_method_name, None)
        if not api_method:
            raise ValueError(f"API method '{self.api_method_name}' not found in the API package '{self.api_package_name}'.")

        # Call the API method with the payload
        return api_method(**self.payload)

    def needs_update(self):
        """
        Method that check if something was changed from last update / create. Can be overrided.
        """
        return self.remote_instance.payload != self.payload

    def additional_update_check(self):
        """
        Method that can be overridden to do the actual update of one instance so we can add extra conditions
        """
        return True

    def post_update_process(self):
        """
        Override this method to add logic after update when we don't want to decentralize with signals
        """
        pass

    def update(self):
        log_identifier, _ = self.get_identifiers()

        # Send pre-update signal
        remote_instance_pre_update.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

        try:
            logger.debug(f"Updating remote instance with payload: {self.payload}")

            # Attempt to update the remote instance
            response = self.update_remote()
            response_data = self.serialize_response(response)

            self.post_action_payload_modify()

            # Log the successful update
            self.log_action(IntegrationLog.ACTION_UPDATE, response_data, self.payload, log_identifier)

            # Send post-update signal
            remote_instance_post_update.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

            self.post_update_process()

        except Exception as e:
            self.successfully_updated = False
            self.log_error(e, IntegrationLog.ACTION_UPDATE, log_identifier, self.payload)
            raise

        finally:
            logger.debug(f"Finished update process with success status: {self.successfully_updated}")
            self.remote_instance.save()

    def run(self):

        if not self.preflight_check():
            return

        self.set_api()
        self.preflight_process()

        # Handle instance creation logic after preflight processes
        self.handle_remote_instance_creation()

        # Abort if the instance was created / re-created
        if not self.successfully_updated:
            return

        self.build_payload()
        self.customize_payload()
        if self.needs_update() and self.additional_update_check():
            self.update()


class IntegrationInstanceDeleteFactory(IntegrationInstanceOperationMixin):
    local_model_class = None  # The Sila Model
    remote_model_class = None  # The Mirror Model
    delete_field_mapping = {}  # Default mapping for deletion payload
    local_product_map = 'local_instance__product'  # the way we go to the local product from the current instance (if possible)
    delete_remote_instance = True

    # Configurable API details
    api_package_name = None  # The package name (e.g., 'properties')
    api_method_name = 'delete'  # The method name for delete (e.g., 'delete')

    def __init__(self, integration, local_instance=None, api=None, remote_instance=None, **kwargs):
        self.local_instance = local_instance
        self.integration = integration
        self.api = api
        self.payload = {}

        setattr(self, self.integration_key, self.integration.get_real_instance())

        if isinstance(remote_instance, self.remote_model_class):
            self.remote_instance = remote_instance
            self.remote_instance_id = remote_instance.id
        else:
            self.remote_instance_id = remote_instance
            self.remote_instance = self.get_remote_instance()

        self.remote_product = self._determine_remote_product(kwargs)

    def get_remote_instance(self):
        """
        Retrieves the remote instance using the local instance and sales channel,
        or directly by remote_instance_id if provided.

        Raises an error if the remote instance is not found.
        """
        try:
            if not hasattr(self, 'remote_instance') or self.remote_instance is None:
                if self.remote_instance_id is not None:
                    instance = self.remote_model_class.objects.get(id=self.remote_instance_id)
                else:
                    get_payload = {
                        'local_instance': self.local_instance,
                        self.integration_key: self.integration
                    }
                    instance = self.remote_model_class.objects.get(**get_payload)

            else:
                instance = self.remote_instance

            logger.debug(f"Fetched remote instance: {instance}")
            return instance
        except self.remote_model_class.DoesNotExist:
            logger.error(f"Integration instance does not exist for {self.local_instance}")
            raise ValueError("Integration instance does not exist.")

    def build_delete_payload(self):
        """
        Constructs the payload for the delete request using the delete_field_mapping.
        This allows flexibility in specifying different identifiers for deletion.
        """
        for local_field, remote_field in self.delete_field_mapping.items():
            self.payload[remote_field] = getattr(self.remote_instance, local_field, None)
        return self.payload

    def delete_remote(self):
        """
        Implements the remote deletion logic using the API client.
        This method deletes the actual remote object on the external system.
        """
        # Retrieve the API package (e.g., 'properties')
        api_package = getattr(self.api, self.api_package_name, None)
        if not api_package:
            raise ValueError(f"API package '{self.api_package_name}' not found in the API client.")

        # Retrieve the API method (e.g., 'delete')
        api_method = getattr(api_package, self.api_method_name, None)
        if not api_method:
            raise ValueError(f"API method '{self.api_method_name}' not found in the API package '{self.api_package_name}'.")

        # Call the API method with the dynamically built payload
        return api_method(**self.payload)

    def delete(self):
        """
        Main method to orchestrate the deletion process, including error handling.
        """
        log_identifier, _ = self.get_identifiers()
        remote_instance_pre_delete.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

        try:
            logger.debug(f"Deleting remote instance with payload: {self.payload}")

            # Attempt to delete the remote instance
            response = self.delete_remote()
            response_data = self.serialize_response(response)

            self.log_action(IntegrationLog.ACTION_DELETE, response_data, self.payload, log_identifier)

        except Exception as e:
            self.log_error(e, IntegrationLog.ACTION_DELETE, log_identifier, self.payload)
            raise

        finally:
            # Send post-delete signal
            remote_instance_post_delete.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

    def delete_remote_instance_process(self):

        if self.delete_remote_instance:
            logger.debug(f"Deleting remote instance: {self.remote_instance}")
            self.remote_instance.delete()

    def preflight_process(self):
        pass

    def run(self):
        """
        Orchestrates the deletion steps without containing business logic.
        """
        self.set_api()
        self.build_delete_payload()
        self.customize_payload()
        self.preflight_process()
        self.delete()
        self.delete_remote_instance_process()
