import requests
from ..signals import remote_instance_pre_create, remote_instance_post_create, remote_instance_post_update, remote_instance_pre_update, \
    remote_instance_pre_delete, remote_instance_post_delete
from ..models.log import RemoteLog
import traceback
import inspect


class RemoteInstanceCreateFactory:
    local_model_class = None  # The Sila Model
    remote_model_class = None  # The Mirror Model
    remote_id_map = 'id'  # Default remote ID mapping to get the remote id from the response
    field_mapping = {}  # Mapping of local fields to remote fields, should be overridden in subclasses

    # Configurable API details
    api_package_name = None  # The package name (e.g., 'properties')
    api_method_name = 'create'  # The method name (e.g., 'create')

    def __init__(self, local_instance, sales_channel):
        self.local_instance = local_instance  # Instance of the local model
        self.sales_channel = sales_channel  # Sales channel associated with the sync
        self.successfully_created = True  # Tracks if creation was successful
        self.payload = {}  # Will hold the payload data
        self.remote_instance_data = {}  # Will hold data for initializing the remote instance
        self.api = self.get_api()

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
        Constructs the payload for the remote instance using the field mapping provided.
        """
        for local_field, remote_field in self.field_mapping.items():
            self.payload[remote_field] = getattr(self.local_instance, local_field, None)

        return self.payload

    def get_identifier(self):
        """
        Sets the identifier to reflect the current class and calling method context.
        """
        frame = inspect.currentframe()
        caller = frame.f_back.f_code.co_name
        class_name = self.__class__.__name__
        return f"{class_name}:{caller}"

    def customize_payload(self):
        """
        Override this method to add customizations to the payload.
        """
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
        remote_instance_pre_create.send(sender=self.remote_instance.__class__, instance=self.remote_instance)
        self.remote_instance.save()

    def modify_remote_instance(self, remote_instance):
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

        # Set the remote_id on the local instance (mirror model)
        self.local_instance.remote_id = remote_id

    def get_api(self):
        """
        Retrieves the API client or wrapper based on the sales channel.
        This method should be overridden to return the appropriate API client.
        """
        # Example: return self.sales_channel.get_api_client()
        raise NotImplementedError("Subclasses must implement the get_api method to return the API client.")

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

    def serialize_response(self, response: requests.Response):
        return response.json()

    def create(self):
        """
        Main method to orchestrate the creation process, including error handling and logging.
        """
        log_identifier = self.get_identifier()

        try:
            # Attempt to create the remote instance
            response = self.create_remote()
            response_data = self.serialize_response(response)
            self.set_remote_id(response_data)

            # Log the successful creation
            self.remote_instance.add_log(
                action=RemoteLog.ACTION_CREATE,
                response=response_data,
                payload=self.payload,
                identifier=log_identifier
            )

            # Send post-create signal
            remote_instance_post_create.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

        except self.sales_channel._meta.user_exceptions as e:
            self.successfully_created = False
            tb = traceback.format_exc()

            # Log the user exception
            self.remote_instance.add_user_error(
                action=RemoteLog.ACTION_CREATE,
                response=str(e),
                payload=self.payload,
                error_traceback=tb,
                identifier=log_identifier
            )
            raise

        except Exception as e:
            self.successfully_created = False
            tb = traceback.format_exc()

            # Log the admin exception
            self.remote_instance.add_admin_error(
                action=RemoteLog.ACTION_CREATE,
                response=str(e),
                payload=self.payload,
                error_traceback=tb,
                identifier=log_identifier
            )

            raise

        finally:
            self.remote_instance.successfully_created = self.successfully_created
            self.remote_instance.save()

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


class RemoteInstanceUpdateFactory:
    local_model_class = None  # The Sila Model
    remote_model_class = None  # The Mirror Model
    remote_id_map = 'id'  # Default remote ID mapping to get the remote id from the response
    field_mapping = {}  # Mapping of local fields to remote fields, should be overridden in subclasses
    updatable_fields = []  # Fields that are allowed to be updated

    # Configurable API details
    api_package_name = None  # The package name (e.g., 'properties')
    api_method_name = 'update'  # The method name (e.g., 'update')

    # Configurable Create Factory for recreating instances if needed
    create_factory_class = None  # Should be overridden in subclasses with the specific Create Factory
    create_if_not_exists = False  # Configurable parameter to create the instance if not found

    def __init__(self, local_instance, sales_channel):
        self.local_instance = local_instance  # Instance of the local model
        self.sales_channel = sales_channel  # Sales channel associated with the sync
        self.successfully_updated = True  # Tracks if update was successful
        self.payload = {}  # Will hold the payload data
        self.api = self.get_api()

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
            self.remote_instance = self.remote_model_class.objects.get(
                local_instance=self.local_instance,
                sales_channel=self.sales_channel
            )

            if not self.remote_instance.successfully_created:
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
        """
        if hasattr(self, 'updatable_fields') and self.updatable_fields:
            # Only include fields specified in updatable_fields if provided
            self.payload = {
                remote_field: getattr(self.local_instance, local_field, None)
                for local_field, remote_field in self.field_mapping.items()
                if local_field in self.updatable_fields
            }
        else:
            # Include all fields from the field mapping if updatable_fields is not specified
            self.payload = {
                remote_field: getattr(self.local_instance, local_field, None)
                for local_field, remote_field in self.field_mapping.items()
            }
        return self.payload

    def customize_payload(self):
        """
        Override this method to add customizations to the payload.
        """
        return self.payload

    def get_api(self):
        """
        Retrieves the API client or wrapper based on the sales channel.
        This method should be overridden to return the appropriate API client.
        """
        # Example: return self.sales_channel.get_api_client()
        raise NotImplementedError("Subclasses must implement the get_api method to return the API client.")

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

    def serialize_response(self, response: requests.Response):
        return response.json()

    def additional_update_check(self):
        """
        Method that can be overridden to do the actual update of one instance so we can add extra conditions
        """
        return True

    def update(self):
        log_identifier = f"{self.__class__.__name__}:update"

        # Send pre-update signal
        remote_instance_pre_update.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

        try:
            # Attempt to update the remote instance
            response = self.update_remote()
            response_data = self.serialize_response(response)

            # Log the successful update
            self.remote_instance.add_log(
                action=RemoteLog.ACTION_UPDATE,
                response=response_data,
                payload=self.payload,
                identifier=log_identifier
            )

            # Send post-update signal
            remote_instance_post_update.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

        except self.sales_channel._meta.user_exceptions as e:
            self.successfully_updated = False
            tb = traceback.format_exc()

            # Log the user exception
            self.remote_instance.add_user_error(
                action=RemoteLog.ACTION_UPDATE,
                response=str(e),
                payload=self.payload,
                error_traceback=tb,
                identifier=log_identifier
            )
            raise

        except Exception as e:
            self.successfully_updated = False
            tb = traceback.format_exc()

            # Log the admin exception
            self.remote_instance.add_admin_error(
                action=RemoteLog.ACTION_UPDATE,
                response=str(e),
                payload=self.payload,
                error_traceback=tb,
                identifier=log_identifier
            )

            raise

    def run(self):
        if not self.preflight_check():
            return

        self.preflight_process()
        self.get_remote_instance()

        # Abort if the instance was re-created
        if not self.successfully_updated:
            return

        self.build_payload()
        self.customize_payload()

        if self.remote_instance.payload != self.payload and self.additional_update_check():
            self.update()


class RemoteInstanceDeleteFactory:
    local_model_class = None  # The Sila Model
    remote_model_class = None  # The Mirror Model
    delete_field_mapping = {'remote_id': 'remote_id'}  # Default mapping for deletion payload

    # Configurable API details
    api_package_name = None  # The package name (e.g., 'properties')
    api_method_name = 'delete'  # The method name for delete (e.g., 'delete')
    api_get_method_name = 'get'  # The method name for get (e.g., 'get')

    def __init__(self, local_instance, sales_channel):
        self.local_instance = local_instance
        self.sales_channel = sales_channel
        self.api = self.get_api()
        self.remote_instance = self.get_remote_instance()

    def get_api(self):
        """
        Retrieves the API client or wrapper based on the sales channel.
        This method should be overridden to return the appropriate API client.
        """
        # Example: return self.sales_channel.get_api_client()
        raise NotImplementedError("Subclasses must implement the get_api method to return the API client.")

    def get_remote_instance(self):
        """
        Retrieves the remote instance using the local instance and sales channel.
        Raises an error if the remote instance is not found.
        """
        try:
            return self.remote_model_class.objects.get(local_instance=self.local_instance, sales_channel=self.sales_channel)
        except self.remote_model_class.DoesNotExist:
            raise ValueError("Remote instance does not exist for deletion.")

    def build_delete_payload(self):
        """
        Constructs the payload for the delete request using the delete_field_mapping.
        This allows flexibility in specifying different identifiers for deletion.
        """
        payload = {}
        for local_field, remote_field in self.delete_field_mapping.items():
            payload[remote_field] = getattr(self.remote_instance, local_field, None)
        return payload

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
        return api_method(**self.build_delete_payload())

    def get_remote(self):
        """
        Tries to fetch the remote instance using the API client to confirm its existence.
        This method is used for validation when deletion fails.
        """
        # Retrieve the API package (e.g., 'properties')
        api_package = getattr(self.api, self.api_package_name, None)
        if not api_package:
            raise ValueError(f"API package '{self.api_package_name}' not found in the API client.")

        # Retrieve the API get method (e.g., 'get')
        api_get_method = getattr(api_package, self.api_get_method_name, None)
        if not api_get_method:
            raise ValueError(f"API method '{self.api_get_method_name}' not found in the API package '{self.api_package_name}'.")

        # Call the API get method with the appropriate identifier
        return api_get_method(**self.build_delete_payload())

    def delete(self):
        """
        Main method to orchestrate the deletion process, including error handling.
        """
        # Send pre-delete signal
        remote_instance_pre_delete.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

        try:
            # Attempt to delete the remote instance
            self.delete_remote()

        except Exception as e:
            # Try to fetch the remote instance to verify if it exists
            try:
                response = self.get_remote()
                if response:
                    raise ValueError(f"Instance deletion failed for {self.remote_instance.remote_id}")
            except Exception:
                # If get fails, the instance likely never existed; no need to log or raise further.
                pass
        finally:
            # Send post-delete signal
            remote_instance_post_delete.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

    def run(self):
        """
        Orchestrates the deletion steps without containing business logic.
        """
        self.delete()


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
                self.local_property,
                self.sales_channel
            )
            property_create_factory.run()

            self.remote_property = property_create_factory.remote_instance