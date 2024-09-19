from products.models import Product
from sales_channels.factories.mixins import RemoteInstanceUpdateFactory, ProductAssignmentMixin

class RemoteProductContentUpdateFactory(RemoteInstanceUpdateFactory, ProductAssignmentMixin):
    local_model_class = Product

    def __init__(self, sales_channel, local_instance, api=None, skip_checks=False, remote_product=None, remote_instance=None):
        self.remote_product = remote_product or self.get_remote_product(local_instance.product)
        self.remote_instance = remote_instance

        if skip_checks and (self.remote_product is None or self.remote_instance is None):
            raise ValueError("Factory has skip checks enabled without providing the remote product.")

        self.skip_checks = skip_checks
        super().__init__(sales_channel, local_instance, api=api)


    def preflight_check(self):
        """
        Checks that the RemoteProduct and associated SalesChannelViewAssign exist before proceeding.
        Also sets the remote_instance if conditions are met.
        """
        if self.skip_checks:
            return True

        if not self.remote_product:
            return False

        if not self.assigned_to_website():
            return False

        # Set the remote_instance for the factory based on existing data
        try:
            self.remote_instance = self.remote_model_class.objects.get(
                remote_product=self.remote_product
            )
        except self.remote_model_class.DoesNotExist:
            return False

        return True

    def get_remote_instance(self):
        """
        Override to prevent fetching in the default way since it is already set in preflight_check.
        """
        pass
