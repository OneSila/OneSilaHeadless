from core.helpers import get_nested_attr, clean_json_data
from ..models.products import RemoteProduct
from ..models.sales_channels import SalesChannelViewAssign
from ..signals import remote_instance_pre_create, remote_instance_post_create, remote_instance_post_update, remote_instance_pre_update, \
    remote_instance_pre_delete, remote_instance_post_delete
from ..models.log import RemoteLog
import traceback
import inspect
import logging

logger = logging.getLogger(__name__)

class RemoteInstanceOperationMixin:
    """
    Mixin providing common operations for remote instance factories.
    Includes methods for API interaction, response handling, logging, and error management.
    """

    def get_api(self):
        """
        Retrieves the API client or wrapper based on the sales channel.
        This method should be overridden to return the appropriate API client.
        """
        raise NotImplementedError("Subclasses must implement the get_api method to return the API client.")

    def serialize_response(self, response):
        """
        Serializes the response from the remote API.
        """
        return response.json()

    def get_identifier(self):
        """
        Generates a log identifier to reflect the current class and calling method context.
        """
        frame = inspect.currentframe()
        caller = frame.f_back.f_code.co_name
        class_name = self.__class__.__name__
        return f"{class_name}:{caller}"

    def log_action_for_instance(self, remote_instance, action, response_data, payload, identifier):
        if not remote_instance:
            raise ValueError("A valid remote_instance must be provided for logging.")

        remote_instance.add_log(
            action=action,
            response=response_data,
            payload=payload,
            identifier=identifier
        )

    def log_action(self, action, response_data, payload, identifier):
        """
        Logs actions for remote instance operations.
        """
        self.remote_instance.add_log(
            action=action,
            response=response_data,
            payload=payload,
            identifier=identifier
        )

    def log_error(self, exception, action, identifier, payload):
        """
        Logs errors for user exceptions or admin exceptions depending on the exception type.
        """
        tb = traceback.format_exc()
        error_message = str(exception)
        payload = clean_json_data(payload)

        if isinstance(exception, self.sales_channel._meta.user_exceptions):
            self.remote_instance.add_user_error(
                action=action,
                response=error_message,
                payload=payload,
                error_traceback=tb,
                identifier=identifier
            )
        else:
            self.remote_instance.add_admin_error(
                action=action,
                response=error_message,
                payload=payload,
                error_traceback=tb,
                identifier=identifier
            )

    def customize_payload(self):
        """
        Override this method to add customizations to the payload.
        """
        return self.payload

class RemoteInstanceCreateFactory(RemoteInstanceOperationMixin):
    local_model_class = None  # The Sila Model
    remote_model_class = None  # The Mirror Model
    remote_id_map = 'id'  # Default remote ID mapping to get the remote id from the response
    field_mapping = {}  # Mapping of local fields to remote fields, should be overridden in subclasses

    # Configurable API details
    api_package_name = None  # The package name (e.g., 'properties')
    api_method_name = 'create'  # The method name (e.g., 'create')

    def __init__(self, sales_channel, local_instance=None, api=None):
        self.local_instance = local_instance  # Instance of the local model
        self.sales_channel = sales_channel  # Sales channel associated with the sync
        self.successfully_created = True  # Tracks if creation was successful
        self.payload = {}  # Will hold the payload data
        self.remote_instance_data = {}  # Will hold data for initializing the remote instance
        self.api = api if api is not None else self.get_api()

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

        return self.payload

    def build_remote_instance_data(self):
        """
        Constructs the data for initializing the remote instance, using local_instance.
        """
        self.remote_instance_data = {'local_instance': self.local_instance, 'sales_channel': self.sales_channel}
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
        self.remote_instance = self.remote_model_class(**self.remote_instance_data)
        self.remote_instance.multi_tenant_company = self.sales_channel.multi_tenant_company
        remote_instance_pre_create.send(sender=self.remote_instance.__class__, instance=self.remote_instance)
        self.remote_instance.save()
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
        id_path = self.remote_id_map.split('__')
        remote_id = response_data

        for path in id_path:
            remote_id = remote_id.get(path, None)
            if remote_id is None:
                break

        # Set the remote_id on the remote instance
        self.remote_instance.remote_id = remote_id

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

    def create(self):
        """
        Main method to orchestrate the creation process, including error handling and logging.
        """
        log_identifier = self.get_identifier()

        try:
            logger.debug(f"Creating remote instance with payload: {self.payload}")

            # Attempt to create the remote instance
            response = self.create_remote()
            response_data = self.serialize_response(response)
            self.set_remote_id(response_data)
            self.modify_remote_instance(response_data)

            # Log the successful creation
            self.log_action(RemoteLog.ACTION_CREATE, response_data, self.payload, log_identifier)

            # Send post-create signal
            remote_instance_post_create.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

            self.post_create_process()

        except Exception as e:
            self.successfully_created = False
            self.log_error(e, RemoteLog.ACTION_CREATE, log_identifier, self.payload)

            raise

        finally:
            self.remote_instance.successfully_created = self.successfully_created
            self.remote_instance.save()
            logger.debug(f"Finished create process with success status: {self.successfully_created}")

    def run(self):

        if not self.preflight_check():
            return

        self.preflight_process()
        self.build_payload()
        self.customize_payload()
        self.build_remote_instance_data()
        self.customize_remote_instance_data()
        self.initialize_remote_instance()
        self.create()


class RemoteInstanceUpdateFactory(RemoteInstanceOperationMixin):
    local_model_class = None  # The Sila Model
    remote_model_class = None  # The Mirror Model
    field_mapping = {}  # Mapping of local fields to remote fields, should be overridden in subclasses
    updatable_fields = []  # Fields that are allowed to be updated

    # Configurable API details
    api_package_name = None  # The package name (e.g., 'properties')
    api_method_name = 'update'  # The method name (e.g., 'update')

    # Configurable Create Factory for recreating instances if needed
    create_factory_class = None  # Should be overridden in subclasses with the specific Create Factory
    create_if_not_exists = False  # Configurable parameter to create the instance if not found

    def __init__(self, sales_channel, local_instance=None, api=None, remote_instance=None):
        self.local_instance = local_instance  # Instance of the local model
        self.sales_channel = sales_channel  # Sales channel associated with the sync
        self.successfully_updated = True  # Tracks if update was successful
        self.payload = {}  # Will hold the payload data
        self.api = api if api is not None else self.get_api()

        # we can give both the remote_instance as an id (from tasks) or the real instance
        if isinstance(remote_instance, self.remote_model_class):
            self.remote_instance = remote_instance
            self.remote_instance_id = remote_instance.id
        else:
            self.remote_instance = None
            self.remote_instance_id = remote_instance

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
        Attempt to recover if the instance was not created successfully.
        """
        try:

            if self.remote_instance is None:
                if self.remote_instance_id is not None:
                    self.remote_instance  = self.remote_model_class.objects.get(id=self.remote_instance_id)
                else:
                    self.remote_instance = self.remote_model_class.objects.get(
                        local_instance=self.local_instance,
                        sales_channel=self.sales_channel)

            logger.debug(f"Fetched remote instance: {self.remote_instance}")

            if not self.remote_instance.successfully_created:
                logger.debug(f"Remote instance not found, attempting to create for {self.local_instance}")
                self.remote_instance.delete()
                # Attempt to "repair" by recreating the remote instance
                self.create_remote_instance()
                # Abort the update after re-creation attempt
                self.successfully_updated = False

        except self.remote_model_class.DoesNotExist:
            if self.create_if_not_exists:
                self.create_remote_instance()
                self.successfully_updated = False
            else:
                raise ValueError(f"Remote instance for value {self.local_instance} does not exist on website {self.sales_channel} and cannot be updated.")

    def create_remote_instance(self):
        """
        Attempts to recreate the remote instance using the specified Create Factory.
        """
        if not self.create_factory_class:
            raise ValueError("Create factory class must be specified to recreate remote instances.")

        create_factory = self.create_factory_class(self.local_instance, self.sales_channel)
        create_factory.run()

        # Refresh the remote instance after attempted creation
        self.remote_instance = self.remote_model_class.objects.get(
            local_instance=self.local_instance,
            sales_channel=self.sales_channel
        )

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
        log_identifier = self.get_identifier()

        # Send pre-update signal
        remote_instance_pre_update.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

        try:
            logger.debug(f"Updating remote instance with payload: {self.payload}")

            # Attempt to update the remote instance
            response = self.update_remote()
            response_data = self.serialize_response(response)

            # Log the successful update
            self.log_action(RemoteLog.ACTION_UPDATE, response_data, self.payload, log_identifier)

            # Send post-update signal
            remote_instance_post_update.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

            self.post_update_process()

        except Exception as e:
            self.successfully_updated = False
            self.log_error(e, RemoteLog.ACTION_UPDATE, log_identifier, self.payload)
            raise

        finally:
            logger.debug(f"Finished update process with success status: {self.successfully_updated}")

    def run(self):
        if not self.preflight_check():
            return

        self.preflight_process()
        self.get_remote_instance()

        # Abort if the instance was created / re-created
        if not self.successfully_updated:
            return

        self.build_payload()
        self.customize_payload()

        if self.needs_update() and self.additional_update_check():
            self.update()


class RemoteInstanceDeleteFactory(RemoteInstanceOperationMixin):
    local_model_class = None  # The Sila Model
    remote_model_class = None  # The Mirror Model
    delete_field_mapping = {}  # Default mapping for deletion payload
    delete_remote_instance = True

    # Configurable API details
    api_package_name = None  # The package name (e.g., 'properties')
    api_method_name = 'delete'  # The method name for delete (e.g., 'delete')

    def __init__(self, sales_channel, local_instance=None, api=None, remote_instance=None):
        self.local_instance = local_instance
        self.sales_channel = sales_channel
        self.api = api if api is not None else self.get_api()
        self.payload = {}

        if isinstance(remote_instance, self.remote_model_class):
            self.remote_instance = remote_instance
            self.remote_instance_id = remote_instance.id
        else:
            self.remote_instance_id = remote_instance
            self.remote_instance = self.get_remote_instance()

    def get_remote_instance(self):
        """
        Retrieves the remote instance using the local instance and sales channel,
        or directly by remote_instance_id if provided.

        Raises an error if the remote instance is not found.
        """
        try:
            if self.remote_instance is None:
                if self.remote_instance_id is not None:
                    instance = self.remote_model_class.objects.get(id=self.remote_instance_id)
                else:
                    instance = self.remote_model_class.objects.get(
                        local_instance=self.local_instance,
                        sales_channel=self.sales_channel
                    )
            else:
                instance = self.remote_instance

            logger.debug(f"Fetched remote instance: {instance}")
            return instance
        except self.remote_model_class.DoesNotExist:
            logger.error(f"Remote instance does not exist for {self.local_instance}")
            raise ValueError("Remote instance does not exist.")

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
        log_identifier = self.get_identifier()
        remote_instance_pre_delete.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

        try:
            logger.debug(f"Deleting remote instance with payload: {self.payload}")

            # Attempt to delete the remote instance
            response = self.delete_remote()
            response_data = self.serialize_response(response)

            self.log_action(RemoteLog.ACTION_DELETE, response_data, self.payload, log_identifier)

        except Exception as e:
            self.log_error(e, RemoteLog.ACTION_DELETE, log_identifier, self.payload)
            raise

        finally:
            # Send post-delete signal
            remote_instance_post_delete.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

    def delete_remote_instance_process(self):
        if self.delete_remote_instance:
            logger.debug(f"Deleting remote instance: {self.remote_instance}")
            self.remote_instance.delete()

    def run(self):
        """
        Orchestrates the deletion steps without containing business logic.
        """
        self.build_delete_payload()
        self.customize_payload()
        self.delete()
        self.delete_remote_instance_process()


class ProductAssignmentMixin:
    """
    Mixin to assist with retrieving RemoteProduct instances and checking their
    assignment status to websites (sales channels).
    """

    def get_remote_product(self, product):
        """
        Retrieves the RemoteProduct associated with the given product.

        Args:
            product: The local Product instance to find the corresponding RemoteProduct.
            sales_channel: The sales channel for which the RemoteProduct should be retrieved.

        Returns:
            The RemoteProduct instance if found, otherwise None.
        """
        try:
            return RemoteProduct.objects.get(
                local_instance=product,
                sales_channel=self.sales_channel
            )
        except RemoteProduct.DoesNotExist:
            return None

    def assigned_to_website(self):
        """
        Checks whether the RemoteProduct and its associated SalesChannelViewAssign exist.

        This method verifies:
        - If the remote product itself is assigned to a website.
        - If the remote product is a variation, checks if its parent product is assigned to a website.

        Returns:
            bool: True if the remote product or its parent is assigned to a website, False otherwise.
        """
        # Ensure that remote_product is set for the instance using this mixin
        if not hasattr(self, 'remote_product') or not self.remote_product:
            return False

        # Check for SalesChannelViewAssign associated with the remote product
        assign_exists = SalesChannelViewAssign.objects.filter(
            product=self.remote_product.local_instance,
            remote_product=self.remote_product,
            sales_channel=self.sales_channel
        ).exists()

        # If the product is a variation, also check the parent product's assign
        if not assign_exists and self.remote_product.is_variation and self.remote_product.remote_parent_product:
            assign_exists = SalesChannelViewAssign.objects.filter(
                product=self.remote_product.remote_parent_product.local_instance,
                remote_product=self.remote_product.remote_parent_product,
                sales_channel=self.sales_channel
            ).exists()

        return assign_exists


class RemotePropertyEnsureMixin:
    def preflight_process(self):
        """
        Ensures that the associated RemoteProperty exists; creates it if not.
        """
        try:
            # Attempt to get the associated RemoteProperty instance using self.local_property
            self.remote_property = self.remote_property_factory.remote_model_class.objects.get(
                local_instance=self.local_property,
                sales_channel=self.sales_channel
            )
        except self.remote_property_factory.remote_model_class.DoesNotExist:
            # If the RemoteProperty does not exist, create it using the provided factory
            property_create_factory = self.remote_property_factory(
                self.sales_channel,
                self.local_property,
            )
            property_create_factory.run()

            self.remote_property = property_create_factory.remote_instance


class PullRemoteInstanceMixin(RemoteInstanceOperationMixin):
    remote_model_class = None  # The Mirror Model (e.g., RemoteOrder)
    field_mapping = {}  # Mapping of remote fields to local fields
    update_field_mapping = {}  # Sometime we want to update only certain fields not all that been created
    api_package_name = None  # The package name (e.g., 'properties')
    api_method_name = None  # The method name (e.g., 'fetch')
    api_method_is_property = False # for some integrations this can be a property / field not a method
    get_or_create_fields = []  # Fields used by get_or_create operations

    allow_create = True  # Allow creation of new instances
    allow_update = True  # Allow updates to existing instances
    allow_delete = False  # Allow deletion of instances no longer present in remote data

    is_model_response = False  # Determines if remote data is a model instance

    def __init__(self, sales_channel, api=None):
        self.sales_channel = sales_channel
        self.api = api if api is not None else self.get_api()
        self.payload = {}  # Will hold the payload data for the API request
        self.remote_instances = []  # List to hold data fetched from the remote system

    def preflight_check(self):
        """
        Perform preliminary checks before proceeding with any operation.
        Default implementation checks if the sales channel is active.
        """
        return self.sales_channel.active

    def build_payload(self):
        """
        Constructs the payload for the API request.
        Override this method in subclasses for custom payload construction.
        """
        self.payload = {}
        return self.payload

    def fetch_remote_instances(self):
        """
        Fetch remote instances by calling the configured API method with the built payload.
        """
        api_package = getattr(self.api, self.api_package_name, None)
        if not api_package:
            raise ValueError(f"API package '{self.api_package_name}' not found in the API client.")
        api_method = getattr(api_package, self.api_method_name, None)
        if not api_method:
            raise ValueError(f"API method '{self.api_method_name}' not found in the API package '{self.api_package_name}'.")

        if self.api_method_is_property:
            response = api_method
        else:
            response = api_method(**self.payload)

        self.remote_instances = self.serialize_response(response)
        logger.debug(f"Fetched remote instances: {self.remote_instances}")

    def allow_process(self, remote_data):
        """
        Determines whether a remote instance should be processed.
        Override this method to implement custom filtering logic.

        :param remote_data: The data for the remote instance being processed.
        :return: True if the instance should be processed, False otherwise.
        """
        return True

    def process_remote_instances(self):
        """
        Processes each remote instance according to the configured rules for creation, updating, and deletion.
        """
        existing_remote_ids = set()
        for remote_data in self.remote_instances:

            # Check if the remote instance should be processed
            if not self.allow_process(remote_data):
                logger.debug(f"Skipping processing for remote data: {remote_data}")
                continue

            identifier = self.get_identifier()
            remote_instance_mirror, created = self.get_or_create_remote_instance_mirror(remote_data)
            if created:
                if self.allow_create:
                    self.create_remote_instance_mirror(remote_data, remote_instance_mirror)
                    self.log_action_for_instance(remote_instance_mirror, RemoteLog.ACTION_CREATE, remote_data, self.payload, identifier)
                else:
                    logger.debug(f"Creation not allowed for {remote_data}")
            else:
                if self.allow_update and self.needs_update(remote_instance_mirror, remote_data):
                    self.update_remote_instance_mirror(remote_data, remote_instance_mirror)
                    self.log_action_for_instance(remote_instance_mirror, RemoteLog.ACTION_UPDATE, remote_data, self.payload, identifier)

            existing_remote_ids.add(remote_instance_mirror.remote_id)

            self.process_remote_instance(remote_data, remote_instance_mirror, created)

        if self.allow_delete:
            self.delete_missing_remote_instance_mirrors(existing_remote_ids)

    def get_remote_field_value(self, remote_data, remote_field):
        """
        Retrieves the value of a field from the remote data.
        Uses getattr if `is_model_response` is True, otherwise uses get() for dict-like access.
        """
        if self.is_model_response:
            return getattr(remote_data, remote_field, None)
        else:
            return remote_data.get(remote_field)

    def update_get_or_create_lookup(self, lookup, remote_data):
        """
        Allows us add extra fields to the get_or_create method from outside
        """
        return lookup

    def get_or_create_remote_instance_mirror(self, remote_data):
        """
        Fetches or creates the mirror instance based on `get_or_create_fields`.
        """
        lookup = {field: self.get_remote_field_value(remote_data, remote_field)
                  for field, remote_field in self.field_mapping.items() if field in self.get_or_create_fields}
        lookup['sales_channel'] = self.sales_channel
        lookup['multi_tenant_company'] = self.sales_channel.multi_tenant_company
        lookup = self.update_get_or_create_lookup(lookup, remote_data)
        return self.remote_model_class.objects.get_or_create(**lookup)

    def create_remote_instance_mirror(self, remote_data, remote_instance_mirror):
        """
        Handles creation of the remote mirror instance.
        Override this method to handle any additional logic during creation.
        """
        for local_field, remote_field in self.field_mapping.items():
            setattr(remote_instance_mirror, local_field, self.get_remote_field_value(remote_data, remote_field))

        remote_instance_mirror.save()
        logger.debug(f"Created remote instance mirror: {remote_instance_mirror}")

    def add_fields_to_remote_instance_mirror(self, remote_data, remote_instance_mirror):
        """
        Before save we can add extra fields to the remote instance.
        """
        pass

    def update_remote_instance_mirror(self, remote_data, remote_instance_mirror):
        """
        Handles updating of the remote mirror instance.
        Override this method to handle any additional logic during updating.
        """
        for local_field, remote_field in self.update_field_mapping.items():
            setattr(remote_instance_mirror, local_field, self.get_remote_field_value(remote_data, remote_field))

        self.add_fields_to_remote_instance_mirror(remote_data, remote_instance_mirror)

        remote_instance_mirror.save()
        logger.debug(f"Updated remote instance mirror: {remote_instance_mirror}")

    def needs_update(self, remote_instance_mirror, remote_data):
        """
        Compares the mirror instance with the remote data to determine if an update is needed.
        Override to implement custom comparison logic.
        """
        for local_field, remote_field in self.update_field_mapping.items():
                if getattr(remote_instance_mirror, local_field) != self.get_remote_field_value(remote_data, remote_field):
                    return True
        return False

    def process_remote_instance(self, remote_data, remote_instance_mirror, created):
        """
        Processes a single remote instance and its corresponding mirror instance.
        Override this method to handle custom processing logic.
        """
        pass

    def delete_missing_remote_instance_mirrors(self, existing_remote_ids):
        """
        Deletes mirror instances that are no longer present in the fetched remote instances.
        """
        for remote_instance_mirror in self.remote_model_class.objects.filter(sales_channel=self.sales_channel):
            if int(remote_instance_mirror.remote_id) not in existing_remote_ids:
                self.log_action_for_instance(remote_instance_mirror, RemoteLog.ACTION_DELETE, {}, {}, self.get_identifier())
                remote_instance_mirror.delete()
                logger.debug(f"Deleted remote instance mirror: {remote_instance_mirror}")


    def run(self):
        """
        Orchestrates the pull process including fetching, processing, and managing mirror instances.
        """
        if not self.preflight_check():
            logger.debug(f"Preflight check failed for {self.sales_channel}")
            return

        self.build_payload()
        self.fetch_remote_instances()
        self.process_remote_instances()