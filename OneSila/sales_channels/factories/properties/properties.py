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


class RemoteProductPropertyCreateFactory(ProductAssignmentMixin, RemotePropertyEnsureMixin, RemoteInstanceCreateFactory):
    local_model_class = ProductProperty
    remote_property_factory = None
    remote_property_select_value_factory = None

    def __init__(self, sales_channel, local_instance, remote_product, api=None, skip_checks=False, get_value_only=False):
        super().__init__(sales_channel, local_instance, api=api)

        self.local_property = local_instance.property
        # instead of creating the it we just receive the value for it so we can add it in bulk on product create
        self.get_value_only = get_value_only
        self.remote_value = None
        self.remote_product = remote_product

        # Ensure remote_product is not None if skip_checks is True
        if skip_checks and self.remote_product is None:
            raise ValueError("Factory has skip checks enabled without providing the remote product.")

        self.skip_checks = skip_checks


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
        self.get_select_values()

    def set_remote_id(self, response_data):
        self.remote_instance.remote_value = str(self.remote_value)

    def customize_remote_instance_data(self):
        self.remote_instance_data['remote_product'] = self.remote_product
        self.remote_instance_data['remote_property'] = self.remote_property
        return self.remote_instance_data

class RemoteProductPropertyUpdateFactory(RemotePropertyEnsureMixin, ProductAssignmentMixin, RemoteInstanceUpdateFactory):
    local_model_class = ProductProperty
    create_if_not_exists = True

    def __init__(self, sales_channel, local_instance, remote_product, api=None, get_value_only=False, remote_instance=None, skip_checks=False):
        super().__init__(sales_channel, local_instance, api=api, remote_instance=remote_instance, remote_product=remote_product)
        self.remote_value = None
        self.remote_property = None
        self.local_property = local_instance.property
        # instead of creating the it we just receive the value for it so we can add it in bulk on product create
        self.get_value_only = get_value_only

        if skip_checks and self.remote_product is None:
            raise ValueError("Factory has skip checks enabled without providing the remote product.")

    def preflight_process(self):
        super().preflight_process()
        self.get_select_values()

    def get_remote_value(self):
        raise NotImplementedError("Subclasses must implement get_remote_value")

    def additional_update_check(self):
        self.local_property = self.local_instance.property
        self.remote_product = self.remote_instance.remote_product
        self.remote_property = self.remote_instance.remote_property

        self.remote_value = self.get_remote_value()

        print('------------------------------')
        print(self.remote_value)
        print(type(self.remote_value))

        # we got the value we stop de process so everything is resolved
        if self.get_value_only:
            return False

        return self.remote_instance.needs_update(self.remote_value)

    def needs_update(self):
        return True


class RemoteProductPropertyDeleteFactory(RemoteInstanceDeleteFactory):
    local_model_class = ProductProperty

    def __init__(self, sales_channel, local_instance, remote_product, api=None,remote_instance=None):
        super().__init__(sales_channel, local_instance, api=api, remote_instance=remote_instance, remote_product=remote_product)