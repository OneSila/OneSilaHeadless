from products.models import Product
from sales_channels.factories.mixins import RemoteInstanceUpdateFactory, ProductAssignmentMixin, EanCodeValueMixin

class RemoteEanCodeUpdateFactory(ProductAssignmentMixin, EanCodeValueMixin, RemoteInstanceUpdateFactory):
    """
    Generic factory for updating a remote EAN code.
    This factory follows the same pattern as RemoteProductContentUpdateFactory,
    with support for skip_checks.
    """
    local_model_class = Product
    local_product_map = 'local_instance'

    def __init__(self, sales_channel, local_instance, remote_product, api=None, skip_checks=False, remote_instance=None):
        super().__init__(sales_channel, local_instance, api=api, remote_product=remote_product)
        self.remote_instance = remote_instance

        if skip_checks and (self.remote_product is None or self.remote_instance is None):
            raise ValueError("Factory has skip_checks enabled without providing the remote product or remote instance.")

        self.skip_checks = skip_checks

    def preflight_check(self):
        """
        Checks that the remote product (mirror) exists before proceeding.
        If skip_checks is enabled, bypasses the check.
        """

        if self.skip_checks:
            return True

        if not self.remote_product:
            return False

        if not self.assigned_to_website():
            return False
        try:
            self.remote_instance = self.remote_model_class.objects.get(
                remote_product=self.remote_product
            )
        except self.remote_model_class.DoesNotExist:
            return False

        return True

    def get_remote_instance(self):
        """
        Override to prevent default fetching, since preflight_check sets it.
        """
        pass