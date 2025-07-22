from typing import Optional
from integrations.factories.mixins import IntegrationInstanceOperationMixin, IntegrationInstanceCreateFactory, IntegrationInstanceUpdateFactory, \
    IntegrationInstanceDeleteFactory
from properties.models import Property
from ..models.sales_channels import SalesChannelViewAssign
from ..models.logs import RemoteLog
import logging
from eancodes.models import EanCode
from ..exceptions import PreFlightCheckError
from currencies.models import Currency

logger = logging.getLogger(__name__)


class RemoteInstanceCreateFactory(IntegrationInstanceCreateFactory):
    integration_key = 'sales_channel'
    fixing_identifier_class = None

    def __init__(self, sales_channel, local_instance=None, api=None):
        super().__init__(integration=sales_channel, local_instance=local_instance, api=api)


class RemoteInstanceUpdateFactory(IntegrationInstanceUpdateFactory):
    integration_key = 'sales_channel'
    fixing_identifier_class = None

    def __init__(self, sales_channel, local_instance=None, api=None, remote_instance=None, **kwargs):
        super().__init__(integration=sales_channel, local_instance=local_instance, api=api, remote_instance=remote_instance, **kwargs)


class RemoteInstanceDeleteFactory(IntegrationInstanceDeleteFactory):
    integration_key = 'sales_channel'
    fixing_identifier_class = None

    def __init__(self, sales_channel, local_instance=None, api=None, remote_instance=None, **kwargs):
        super().__init__(integration=sales_channel, local_instance=local_instance, api=api, remote_instance=remote_instance, **kwargs)


class ProductAssignmentMixin:
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

        logger.debug(f"{assign_exists=}, {self.remote_product=}, {self.sales_channel=}")

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
                sales_channel=self.sales_channel,
            )
            logger.info(f"{self.__class__.__name__} preflight_process found and existing remote_property")
        except self.remote_property_factory.remote_model_class.DoesNotExist:
            # If the RemoteProperty does not exist, create it using the provided factory
            property_create_factory = self.remote_property_factory(
                self.sales_channel,
                self.local_property,
                api=self.api
            )
            property_create_factory.run()
            logger.info(f"{self.__class__.__name__} preflight_process tried to create a remote_property")

            self.remote_property = property_create_factory.remote_instance

        if not hasattr(self, 'remote_property') or not self.remote_property:
            # A remote factory should always have a remote_property.
            # If it does not, then most it seem stuff is broken.
            raise PreFlightCheckError(f"Failed to create remote property for {self.local_property}")

    def get_select_values(self):
        self.remote_select_values = []
        # For select or multi-select properties, ensure RemotePropertySelectValue exists
        if self.local_property.type in [Property.TYPES.SELECT, Property.TYPES.MULTISELECT]:
            select_values = self.local_instance.value_multi_select.all() if self.local_property.type == Property.TYPES.MULTISELECT else [
                self.local_instance.value_select]

            for value in select_values:
                try:
                    remote_select_value = self.remote_property_select_value_factory.remote_model_class.objects.get(
                        local_instance=value,
                        sales_channel=self.sales_channel
                    )
                except self.remote_property_select_value_factory.remote_model_class.DoesNotExist:
                    # Create the remote select value if it doesn't exist
                    select_value_create_factory = self.remote_property_select_value_factory(
                        local_instance=value,
                        sales_channel=self.sales_channel,
                        api=self.api
                    )
                    select_value_create_factory.run()
                    remote_select_value = select_value_create_factory.remote_instance

                self.remote_select_values.append(remote_select_value.remote_id)


class PullRemoteInstanceMixin(IntegrationInstanceOperationMixin):
    remote_model_class = None  # The Mirror Model (e.g., RemoteOrder)
    field_mapping = {}  # Mapping of remote fields to local fields
    update_field_mapping = {}  # Sometime we want to update only certain fields not all that been created
    api_package_name = None  # The package name (e.g., 'properties')
    api_method_name = None  # The method name (e.g., 'fetch')
    api_method_is_property = False  # for some integrations this can be a property / field not a method
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

            identifier = self.get_identifiers()
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
                self.log_action_for_instance(remote_instance_mirror, RemoteLog.ACTION_DELETE, {}, {}, self.get_identifiers()[0])
                remote_instance_mirror.delete()
                logger.debug(f"Deleted remote instance mirror: {remote_instance_mirror}")\

    def post_pull_action(self):
        pass

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
        self.post_pull_action()


class EanCodeValueMixin:
    def get_ean_code_value(self) -> Optional[str]:
        ean_obj = EanCode.objects.filter(product=self.local_instance).first()
        return ean_obj.ean_code if ean_obj else None


class SyncProgressMixin:

    def precalculate_progress_step_increment(self, total_steps_excluding_variations: int):
        """
        Calculate the progress increment value for the sync process.

        This method determines the total number of steps by adding:
          - The number of variation items (if any), and
          - The additional steps provided via total_steps_excluding_variations.
        It then divides 100 (the full progress percentage) by the total number of steps.
        The calculated increment is saved in self.increment, and the sync progress is reset to 0.

        :param total_steps_excluding_variations: The number of steps in the sync process that are not
                                                 related to processing variations.
        """
        variations = getattr(self, 'variations', None)
        variations_count = variations.count() if variations is not None else 0
        total_steps = variations_count + total_steps_excluding_variations

        if total_steps <= 0:
            self.increment = 0
        else:
            self.increment = int(100 / total_steps)

        self.current_progress = 0
        self.remote_instance.set_new_sync_percentage(self.current_progress)

    def update_progress(self):

        if self.remote_instance is None:
            return

        self.current_progress = min(self.current_progress + self.increment, 99)
        self.remote_instance.set_new_sync_percentage(self.current_progress)
        logger.debug(f"Updated sync progress to {self.current_progress}%.")

    def finalize_progress(self):

        if self.remote_instance is None:
            return

        self.remote_instance.set_new_sync_percentage(100)


class LocalCurrencyMappingMixin:
    """Mixin to map pulled currency codes to local ``Currency`` instances."""

    def _get_remote_code_field(self) -> str:
        """Return the key used in ``remote_data`` for the currency code."""
        return getattr(self, "field_mapping", {}).get("remote_code", "code")

    def add_local_currency(self) -> None:
        """Attach a matching ``Currency`` instance to each remote record."""
        code_field = self._get_remote_code_field()

        for remote_data in self.remote_instances:
            code = remote_data.get(code_field)
            if not code:
                continue

            currency = Currency.objects.filter(
                iso_code=code,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
            ).first()

            remote_data["local_currency"] = currency
