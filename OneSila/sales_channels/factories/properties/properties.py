from properties.models import Property, PropertySelectValue, ProductProperty
from ..mixins import RemoteInstanceCreateFactory, RemoteInstanceDeleteFactory, RemoteInstanceUpdateFactory, RemotePropertyEnsureMixin, ProductAssignmentMixin


class RemotePropertyCreateFactory(RemoteInstanceCreateFactory):
    local_model_class = Property

class RemotePropertyUpdateFactory(RemoteInstanceUpdateFactory):
    local_model_class = Property
    create_if_not_exists = True

class RemotePropertyDeleteFactory(RemoteInstanceDeleteFactory):
    local_model_class = Property

class RemotePropertySelectValueCreateFactory(RemotePropertyEnsureMixin, RemoteInstanceCreateFactory):
    local_model_class = PropertySelectValue
    remote_property_factory = None

    def __init__(self, local_instance, sales_channel):
        self.local_property = local_instance.property
        super().__init__(local_instance=local_instance, sales_channel=sales_channel)

    def customize_remote_instance_data(self):
        self.remote_instance_data['remote_property'] = self.remote_property
        return self.remote_instance_data

class RemotePropertySelectValueUpdateFactory(RemoteInstanceUpdateFactory):
    local_model_class = PropertySelectValue
    create_if_not_exists = True

class RemotePropertySelectValueDeleteFactory(RemoteInstanceDeleteFactory):
    local_model_class = PropertySelectValue


class RemoteProductPropertyCreateFactory(RemotePropertyEnsureMixin, RemoteInstanceCreateFactory, ProductAssignmentMixin):
    local_model_class = ProductProperty
    remote_property_factory = None
    remote_property_select_value_factory = None

    def __init__(self, sales_channel, local_instance, api=None, skip_checks=False, remote_product=None, get_value_only=False):
        self.local_property = local_instance.property
        # instead of creating the it we just receive the value for it so we can add it in bulk on product create
        self.get_value_only = get_value_only
        self.remote_value = None
        # Assign the remote_product based on the provided parameter or fetch it if None
        self.remote_product = remote_product or self.get_remote_product(local_instance.product)

        # Ensure remote_product is not None if skip_checks is True
        if skip_checks and self.remote_product is None:
            raise ValueError("Factory has skip checks enabled without providing the remote product.")

        self.skip_checks = skip_checks
        super().__init__(sales_channel, local_instance, api=api)


    def preflight_check(self):
        """
        Checks that the RemoteProduct exists before proceeding.
        """
        # If skip_checks is True, always return True
        if self.skip_checks:
            return True

        if not self.remote_product:
            return False

        if not self.assigned_to_website():
            return False

        return True

    def preflight_process(self):
        super().preflight_process()

        self.remote_select_values = []
        # For select or multi-select properties, ensure RemotePropertySelectValue exists
        if self.local_property.type in [Property.TYPES.SELECT, Property.TYPES.MULTISELECT]:
            select_values = self.local_instance.value_select.all() if self.local_property.type == Property.TYPES.MULTISELECT else [self.local_instance.value_select]

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
                        remote_property_factory=self.remote_property_factory
                    )
                    select_value_create_factory.run()
                    remote_select_value = select_value_create_factory.remote_instance

                self.remote_select_values.append(remote_select_value.remote_id)


    def set_remote_id(self, response_data):
        self.remote_instance.remote_value = str(self.remote_value)

    def customize_remote_instance_data(self):
        self.remote_instance_data['remote_product'] = self.remote_product
        self.remote_instance_data['remote_property'] = self.remote_property
        return self.remote_instance_data

class RemoteProductPropertyUpdateFactory(RemoteInstanceUpdateFactory):
    local_model_class = ProductProperty
    create_if_not_exists = True

    def __init__(self, sales_channel, local_instance, api=None, get_value_only=False):
        self.remote_value = None
        self.remote_property = None
        self.remote_product = None
        self.local_property = local_instance.property
        # instead of creating the it we just receive the value for it so we can add it in bulk on product create
        self.get_value_only = get_value_only
        super().__init__(sales_channel, local_instance, api=api)


    def get_remote_value(self):
        raise NotImplementedError("Subclasses must implement get_remote_value")

    def additional_update_check(self):
        self.local_property = self.local_instance.property
        self.remote_product = self.remote_instance.remote_product
        self.remote_property = self.remote_instance.remote_property

        self.remote_value = self.get_remote_value()

        # we got the value we stop de process so everything is resolved
        if self.get_value_only:
            return False

        return self.remote_instance.needs_update(self.remote_value)

    def needs_update(self):
        return True


class RemoteProductPropertyDeleteFactory(RemoteInstanceDeleteFactory):
    local_model_class = ProductProperty