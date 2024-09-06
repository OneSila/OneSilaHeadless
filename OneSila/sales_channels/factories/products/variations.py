from sales_channels.factories.mixins import RemoteInstanceUpdateFactory
from sales_channels.models.product import RemoteProduct
from sales_channels.models.sales_channels import SalesChannelViewAssign


class RemoteProductVariationUpdateFactory(RemoteInstanceUpdateFactory):
    def __init__(self, local_instance, sales_channel, parent_product):
        self.local_instance = local_instance
        self.sales_channel = sales_channel
        self.parent_product = parent_product
        self.remote_instance = None
        self.remote_parent_product = None  # Will be set in the preflight_check
        super().__init__(local_instance, sales_channel)

    def preflight_check(self):
        """
        Checks that the RemoteProduct, Remote Parent Product, and associated SalesChannelViewAssign exist before proceeding.
        Also sets the remote_instance if conditions are met.
        """
        # Retrieve the RemoteProduct associated with the parent local product
        try:
            self.remote_parent_product = RemoteProduct.objects.get(
                local_instance=self.parent_product,
                sales_channel=self.sales_channel
            )
        except RemoteProduct.DoesNotExist:
            return False

        # Check for SalesChannelViewAssign associated with the remote parent product
        parent_assign_exists = SalesChannelViewAssign.objects.filter(
            product=self.parent_product,
            remote_product=self.remote_parent_product
        ).exists()

        # Check if the remote variation product itself exists in the sales channel
        try:
            self.remote_instance = RemoteProduct.objects.get(
                local_instance=self.local_instance,
                sales_channel=self.sales_channel
            )
        except RemoteProduct.DoesNotExist:
            return False

        # Check if the variation product itself has an assign
        variation_assign_exists = SalesChannelViewAssign.objects.filter(
            product=self.local_instance,
            remote_product=self.remote_instance
        ).exists()

        # Return False if any of the required assignments do not exist
        if not parent_assign_exists or not variation_assign_exists:
            return False

        return True

    def get_remote_instance(self):
        pass