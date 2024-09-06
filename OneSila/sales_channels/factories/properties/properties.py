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

    def __init__(self, local_instance, sales_channel, remote_property_factory):
        self.remote_property_factory = remote_property_factory
        self.local_property = local_instance.property
        super().__init__(local_instance, sales_channel)

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

    def __init__(self, local_instance, sales_channel, remote_property_factory, remote_product_factory, remote_property_select_value_factory):
        self.remote_property_factory = remote_property_factory
        self.remote_product_factory = remote_product_factory
        self.remote_property_select_value_factory = remote_property_select_value_factory
        self.local_property = local_instance.property
        self.remote_product = self.get_remote_product(local_instance.product)
        super().__init__(local_instance, sales_channel)


    def preflight_check(self):
        """
        Checks that the RemoteProduct exists before proceeding.
        """
        if not self.remote_product:
            return False

        if not self.assigned_to_website():
            return False

        return True

    def preflight_process(self):
        super().preflight_process()

        # For select or multi-select properties, ensure RemotePropertySelectValue exists
        if self.local_property.type in ['SELECT', 'MULTISELECT']:
            select_values = self.local_instance.value_select.all() if self.local_property.type == 'MULTISELECT' else [self.local_instance.value_select]

            for value in select_values:
                try:
                    self.remote_property_select_value_factory.remote_model_class.objects.get(
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

    def customize_remote_instance_data(self):
        self.remote_instance_data['remote_product'] = self.remote_product
        self.remote_instance_data['remote_property'] = self.remote_property
        return self.remote_instance_data

class RemoteProductPropertyUpdateFactory(RemoteInstanceUpdateFactory):
    local_model_class = ProductProperty
    create_if_not_exists = True

class RemoteProductPropertyDeleteFactory(RemoteInstanceDeleteFactory):
    local_model_class = ProductProperty